from __future__ import annotations

import ast
import json
import multiprocessing as mp
import queue as queue_module
import traceback
from typing import Any

import numpy as np


class AggregationValidationError(ValueError):
    pass


class AggregationExecutionError(RuntimeError):
    pass


# Directly callable names available in generated code.
SAFE_CALL_NAMES = {
    "get",
    "keys",
    "values",
    "items",
    "append",
    "set_item",
    "jsonable",
    "len",
    "range",
    "sum",
    "min",
    "max",
    "abs",
    "float",
    "int",
    "str",
    "bool",
    "round",
    "sorted",
    "enumerate",
    "zip",
    "all",
    "any",
    "list",
    "dict",
    "set",
    "tuple",
}


# Functions and attributes available as np.<name>.
#
# Do not add things such as np.load, np.save, np.fromfile, np.memmap,
# np.ctypeslib, or np.testing here. They are unnecessary for aggregation
# and expand the attack surface.
SAFE_NUMPY_ATTRIBUTES = {
    # Array creation / shape operations
    "array",
    "asarray",
    "zeros",
    "ones",
    "full",
    "empty",
    "arange",
    "linspace",
    "reshape",
    "ravel",
    "flatten",
    "transpose",

    # Matrix and vector operations
    "dot",
    "matmul",
    "einsum",
    "outer",
    "stack",
    "concatenate",
    "vstack",
    "hstack",

    # Elementwise operations
    "maximum",
    "minimum",
    "clip",
    "where",
    "abs",
    "sqrt",
    "exp",
    "log",
    "log1p",

    # Aggregate operations
    "sum",
    "mean",
    "median",
    "std",
    "max",
    "min",
    "argmax",
    "argmin",
    "argsort",
    "unique",
    "all",
    "any",

    # Validation / type conversion
    "isfinite",
    "isnan",
    "float64",
    "float32",
    "int64",
    "int32",
    "bool_",
}


# Methods allowed on local list, dict, set, string, and NumPy-array values.
#
# Attribute access remains restricted. In particular, generated code may not
# access __class__, __globals__, __subclasses__, or arbitrary module members.
SAFE_OBJECT_METHODS = {
    # list methods
    "append",
    "extend",
    "pop",
    "sort",
    "reverse",
    "count",
    "index",

    # dict methods
    "get",
    "items",
    "keys",
    "values",
    "setdefault",
    "update",
    "copy",
    "pop",

    # set methods
    "add",
    "discard",
    "union",
    "intersection",
    "difference",

    # string methods
    "lower",
    "upper",
    "strip",
    "split",
    "replace",
    "startswith",
    "endswith",

    # NumPy array methods
    "tolist",
    "astype",
    "reshape",
    "ravel",
    "flatten",
    "sum",
    "mean",
    "max",
    "min",
    "clip",
    "round",

    # Safe array properties, for example: matrix.shape[0]
    "shape",
    "size",
    "ndim",
    "dtype",
}


ALLOWED_AST_NODES = {
    ast.Module,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,

    # Statements
    ast.Return,
    ast.Assign,
    ast.AugAssign,
    ast.For,
    ast.While,
    ast.If,
    ast.Break,
    ast.Continue,
    ast.Pass,
    ast.Expr,

    # Values and identifiers
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.Dict,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.Subscript,
    ast.Slice,
    ast.Attribute,

    # Comprehensions
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.comprehension,

    # Expressions
    ast.Compare,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.IfExp,
    ast.Call,
    ast.keyword,

    # Comparison operations
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,

    # Boolean operations
    ast.And,
    ast.Or,
    ast.Not,

    # Arithmetic operations
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,

    # Set / bit operations; useful with sets and Boolean vectors.
    ast.BitAnd,
    ast.BitOr,
    ast.BitXor,
}


def _validate_assignment_target(target: ast.AST) -> None:
    """
    Permit:

        x = ...
        scores[i] = ...
        matrix[i, j] = ...

    Do not permit:

        object.attribute = ...
    """

    if isinstance(target, ast.Name):
        if target.id == "np":
            raise AggregationValidationError(
                "The reserved NumPy variable 'np' cannot be reassigned."
            )
        return

    if isinstance(target, ast.Subscript):
        return

    raise AggregationValidationError(
        "Assignments must target a local variable or an indexed list/dict/"
        "array element."
    )


def _validate_attribute_access(node: ast.Attribute) -> None:
    """
    Only allow one-level attribute access:

        np.dot(...)
        scores.tolist()
        output.get(...)

    Reject chained access such as:

        object.__class__.__base__
        np.random.default_rng
        matrix.dtype.name
    """

    if node.attr.startswith("_") or "__" in node.attr:
        raise AggregationValidationError(
            f"Unsafe attribute access: {node.attr}"
        )

    if not isinstance(node.value, ast.Name):
        raise AggregationValidationError(
            "Only one-level attribute access is allowed. "
            "For example, use matrix.tolist(), not x.y.z."
        )

    parent_name = node.value.id

    if parent_name == "np":
        if node.attr not in SAFE_NUMPY_ATTRIBUTES:
            raise AggregationValidationError(
                f"NumPy operation np.{node.attr} is not allowed."
            )
        return

    if node.attr not in SAFE_OBJECT_METHODS:
        raise AggregationValidationError(
            f"Method or attribute .{node.attr} is not allowed."
        )


def validate_aggregation_code(source: str) -> None:
    """
    Validate generated aggregation code before it is executed.

    The function is intentionally more permissive than the original version:
    it permits loops, while loops, ordinary indexing, list/dict methods, and
    a selected safe NumPy API.

    This is still not a complete security boundary. Production execution should
    eventually happen in a container or VM with OS-level network, filesystem,
    CPU, and memory restrictions.
    """

    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise AggregationValidationError(
            f"Aggregation code has invalid Python syntax: {exc}"
        ) from exc

    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise AggregationValidationError(
            "Aggregation code must contain exactly one function definition."
        )

    function = tree.body[0]

    if function.name != "aggregate":
        raise AggregationValidationError(
            "Aggregation function must be named 'aggregate'."
        )

    if function.decorator_list:
        raise AggregationValidationError(
            "Decorators are not allowed in aggregation code."
        )

    argument_names = [arg.arg for arg in function.args.args]

    if argument_names != [
        "question_outputs",
        "survey",
        "responses",
    ]:
        raise AggregationValidationError(
            "Aggregation function must have exactly this signature:\n"
            "def aggregate(question_outputs, survey, responses):"
        )

    if (
        function.args.posonlyargs
        or function.args.vararg is not None
        or function.args.kwarg is not None
        or function.args.kwonlyargs
        or function.args.defaults
        or function.args.kw_defaults
    ):
        raise AggregationValidationError(
            "Aggregation function may not use positional-only, variadic, "
            "keyword-only, or default arguments."
        )

    for node in ast.walk(tree):
        if type(node) not in ALLOWED_AST_NODES:
            raise AggregationValidationError(
                f"Disallowed syntax in aggregation code: "
                f"{type(node).__name__}"
            )

        if isinstance(node, ast.Attribute):
            _validate_attribute_access(node)

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id not in SAFE_CALL_NAMES:
                    raise AggregationValidationError(
                        f"Call to disallowed function: {node.func.id}"
                    )

            elif isinstance(node.func, ast.Attribute):
                _validate_attribute_access(node.func)

            else:
                raise AggregationValidationError(
                    "Only direct calls to approved functions or approved "
                    "one-level methods are allowed."
                )

            if any(keyword.arg is None for keyword in node.keywords):
                raise AggregationValidationError(
                    "Dictionary expansion in function calls is not allowed."
                )

        if isinstance(node, ast.Name):
            if node.id.startswith("_") or "__" in node.id:
                raise AggregationValidationError(
                    f"Unsafe identifier in aggregation code: {node.id}"
                )

        if isinstance(node, ast.Assign):
            for target in node.targets:
                _validate_assignment_target(target)

        if isinstance(node, ast.AugAssign):
            _validate_assignment_target(node.target)

        if isinstance(node, ast.For):
            _validate_assignment_target(node.target)

        if isinstance(node, ast.comprehension):
            if node.is_async:
                raise AggregationValidationError(
                    "Async comprehensions are not allowed."
                )

            _validate_assignment_target(node.target)


def _safe_get(mapping: Any, key: Any, default: Any = None) -> Any:
    if isinstance(mapping, dict):
        return mapping.get(key, default)
    return default


def _safe_keys(mapping: Any) -> list[Any]:
    if isinstance(mapping, dict):
        return list(mapping.keys())
    return []


def _safe_values(mapping: Any) -> list[Any]:
    if isinstance(mapping, dict):
        return list(mapping.values())
    return []


def _safe_items(mapping: Any) -> list[tuple[Any, Any]]:
    if isinstance(mapping, dict):
        return list(mapping.items())
    return []


def _safe_append(sequence: list[Any], value: Any) -> None:
    sequence.append(value)


def _safe_set_item(mapping: dict[Any, Any], key: Any, value: Any) -> None:
    mapping[key] = value


def _to_jsonable(value: Any) -> Any:
    """
    Convert NumPy outputs into ordinary JSON-compatible Python values.

    This allows aggregation code to return NumPy arrays or NumPy scalar values
    directly.
    """

    if isinstance(value, np.ndarray):
        return _to_jsonable(value.tolist())

    if isinstance(value, np.generic):
        return _to_jsonable(value.item())

    if isinstance(value, dict):
        return {
            str(_to_jsonable(key)): _to_jsonable(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _to_jsonable(item)
            for item in value
        ]

    return value


def _safe_globals() -> dict[str, Any]:
    return {
        "__builtins__": {},

        # Preloaded NumPy module. Generated code uses np.array(...), np.dot(...),
        # etc., but must not write "import numpy as np".
        "np": np,

        # Existing helper functions
        "get": _safe_get,
        "keys": _safe_keys,
        "values": _safe_values,
        "items": _safe_items,
        "append": _safe_append,
        "set_item": _safe_set_item,
        "jsonable": _to_jsonable,

        # Safe built-in functions
        "len": len,
        "range": range,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "float": float,
        "int": int,
        "str": str,
        "bool": bool,
        "round": round,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "all": all,
        "any": any,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
    }


def _apply_child_resource_limits() -> None:
    """
    Best-effort resource limits on Unix-like systems.

    Windows does not provide the `resource` module, so Windows relies on the
    parent process timeout unless a stronger external sandbox is used.
    """

    try:
        import resource

        resource.setrlimit(
            resource.RLIMIT_CPU,
            (10, 10),
        )

        memory_limit_bytes = 512 * 1024 * 1024

        resource.setrlimit(
            resource.RLIMIT_AS,
            (memory_limit_bytes, memory_limit_bytes),
        )
    except Exception:
        pass


def _aggregation_worker(
    source: str,
    payload_json: str,
    result_queue: mp.Queue,
) -> None:
    try:
        _apply_child_resource_limits()
        validate_aggregation_code(source)

        namespace = _safe_globals()

        compiled = compile(
            source,
            filename="<generated_aggregation>",
            mode="exec",
        )

        exec(compiled, namespace, namespace)

        aggregate = namespace["aggregate"]
        payload = json.loads(payload_json)

        result = aggregate(
            payload["question_outputs"],
            payload["survey"],
            payload["responses"],
        )

        serialized = json.dumps(
            _to_jsonable(result),
            ensure_ascii=False,
            allow_nan=False,
        )

        result_queue.put(("ok", serialized))

    except Exception:
        result_queue.put(
            (
                "error",
                traceback.format_exc(),
            )
        )


def execute_generated_aggregation(
    *,
    source: str,
    question_outputs: list[dict[str, Any]],
    survey: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    """
    Execute generated aggregation Python in a child process.

    The timeout protects against accidental infinite while loops. The AST
    validator blocks imports and most dangerous constructs, but production
    deployment should eventually use a container-level sandbox.
    """

    validate_aggregation_code(source)

    payload_json = json.dumps(
        {
            "question_outputs": question_outputs,
            "survey": survey,
            "responses": responses,
        },
        ensure_ascii=False,
        allow_nan=False,
    )

    context = mp.get_context("spawn")
    result_queue: mp.Queue = context.Queue()

    process = context.Process(
        target=_aggregation_worker,
        args=(source, payload_json, result_queue),
    )

    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()

        raise AggregationExecutionError(
            "Generated aggregation code exceeded the time limit. "
            "Check for an unbounded while loop."
        )

    try:
        status, payload = result_queue.get(timeout=1.0)
    except queue_module.Empty as exc:
        raise AggregationExecutionError(
            "Generated aggregation process exited without returning a result."
        ) from exc

    if status == "error":
        raise AggregationExecutionError(
            "Generated aggregation code failed:\n"
            f"{payload}"
        )

    result = json.loads(payload)

    if not isinstance(result, dict):
        raise AggregationExecutionError(
            "Aggregation function must return a JSON object."
        )

    return result