from __future__ import annotations

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


def validate_aggregation_code(source: str) -> None:
    """
    Minimal validation for trusted generated code.

    This intentionally does NOT restrict:
    - imports;
    - builtins;
    - attribute access;
    - method chains;
    - while loops;
    - external packages installed in the environment;
    - normal Python syntax.

    It only verifies that the generated source is non-empty and compiles.
    The aggregate() function contract is checked during execution.
    """

    if not isinstance(source, str):
        raise AggregationValidationError(
            "Aggregation code must be a string."
        )

    if not source.strip():
        raise AggregationValidationError(
            "Aggregation code cannot be empty."
        )

    try:
        compile(
            source,
            filename="<generated_aggregation>",
            mode="exec",
        )
    except SyntaxError as exc:
        raise AggregationValidationError(
            f"Aggregation code has invalid Python syntax: {exc}"
        ) from exc


def _to_jsonable(value: Any) -> Any:
    """
    Convert common numerical values into ordinary JSON-compatible values.

    Generated code may return:
    - dicts, lists, strings, numbers, booleans, None;
    - NumPy arrays;
    - NumPy scalar values;
    - tuples and sets.

    The final value must still be JSON serializable, because it becomes the
    input to the deterministic decision function.
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


def _apply_child_resource_limits() -> None:
    """
    Optional best-effort Unix resource limits.

    This is not enabled by default. It can be useful if generated code
    accidentally consumes excessive memory or CPU.

    It does nothing on platforms without the `resource` module, including
    most Windows environments.
    """

    try:
        import resource

        max_memory_bytes = 2 * 1024 * 1024 * 1024
        max_cpu_seconds = 60

        resource.setrlimit(
            resource.RLIMIT_AS,
            (max_memory_bytes, max_memory_bytes),
        )

        resource.setrlimit(
            resource.RLIMIT_CPU,
            (max_cpu_seconds, max_cpu_seconds),
        )
    except Exception:
        pass


def _aggregation_worker(
    source: str,
    payload_json: str,
    result_queue: mp.Queue,
    apply_resource_limits: bool,
) -> None:
    """
    Execute trusted aggregation code in a separate process.

    The generated code has normal Python capabilities:
    - normal builtins;
    - import statements;
    - NumPy;
    - installed packages;
    - normal method access and chained calls.

    For example, all of these are allowed:

        import numpy as np
        import math

        normalized = concept.lower().strip()
        traits_by_id[entity_id].append(trait)
        score = np.dot(a, b)
        matrix = np.asarray(values, dtype=float)
    """

    try:
        if apply_resource_limits:
            _apply_child_resource_limits()

        validate_aggregation_code(source)

        payload = json.loads(payload_json)

        # Do not set "__builtins__" to an empty dictionary.
        #
        # Leaving it absent gives the generated code normal Python builtins,
        # including isinstance, dict, list, set, open, range, etc.
        #
        # np is also preloaded for convenience, although generated code may
        # still write `import numpy as np` if it prefers.
        namespace: dict[str, Any] = {
            "__name__": "__generated_aggregation__",
            "__file__": "<generated_aggregation>",
            "np": np,
        }

        compiled = compile(
            source,
            filename="<generated_aggregation>",
            mode="exec",
        )

        exec(compiled, namespace, namespace)

        aggregate = namespace.get("aggregate")

        if not callable(aggregate):
            raise AggregationExecutionError(
                "Generated aggregation code must define a callable function:\n"
                "def aggregate(question_outputs, survey, responses):"
            )

        result = aggregate(
            payload["question_outputs"],
            payload["survey"],
            payload["responses"],
        )

        if not isinstance(result, dict):
            raise AggregationExecutionError(
                "aggregate() must return a dictionary / JSON object."
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
    timeout_seconds: float | None = 60.0,
    apply_resource_limits: bool = False,
) -> dict[str, Any]:
    """
    Execute trusted LLM-generated aggregation code.

    Parameters
    ----------
    timeout_seconds:
        Maximum execution time. Set to None to disable the timeout entirely.

        Keeping a timeout is recommended even for trusted code because an
        accidental infinite while loop can otherwise hang the pipeline.

    apply_resource_limits:
        If True, apply best-effort CPU/memory limits on Unix systems.
        Defaults to False so ordinary aggregation code is not constrained.
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
        args=(
            source,
            payload_json,
            result_queue,
            apply_resource_limits,
        ),
    )

    process.start()

    if timeout_seconds is None:
        process.join()
    else:
        process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()

        raise AggregationExecutionError(
            "Generated aggregation code exceeded the configured time limit "
            f"of {timeout_seconds} seconds."
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
            "Generated aggregation code did not return a JSON object."
        )

    return result