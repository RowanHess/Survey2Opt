from __future__ import annotations

import math
from typing import Any

import gurobipy as gp
from gurobipy import GRB


BIPARTITE_MATCHING_DOCUMENTATION = """
The decision function solves a maximum-weight bipartite matching problem.

The aggregation function must return one JSON object with exactly these fields:

{
  "left_ids": ["left_entity_id_1", "..."],
  "right_ids": ["right_entity_id_1", "..."],
  "weights": {
    "left_entity_id_1": {
      "right_entity_id_1": 0.0,
      "right_entity_id_2": 1.0
    }
  }
}

Requirements:
- left_ids and right_ids must contain unique string IDs.
- weights must provide a finite numeric weight for every left/right pair.
- The function may leave entities unmatched. If supplying inputs, you should seek to avoid this. Use this option if and only if there is explicit incompatability.
- Each left entity may match with at most one right entity.
- Each right entity may match with at most one left entity.
- Only strictly positive-weight edges are eligible for a match.
- The returned decision maximizes the sum of selected edge weights.

The output is a JSON object containing:
- status,
- objective_value,
- pairs: a list of selected left/right matches and their weights.
""".strip()


def _validate_matching_input(
    optimization_input: dict[str, Any],
) -> tuple[list[str], list[str], dict[str, dict[str, float]]]:
    if not isinstance(optimization_input, dict):
        raise ValueError("Optimization input must be a JSON object.")

    left_ids = optimization_input.get("left_ids")
    right_ids = optimization_input.get("right_ids")
    weights = optimization_input.get("weights")

    if not isinstance(left_ids, list) or not all(
        isinstance(value, str) for value in left_ids
    ):
        raise ValueError("left_ids must be a list of strings.")

    if not isinstance(right_ids, list) or not all(
        isinstance(value, str) for value in right_ids
    ):
        raise ValueError("right_ids must be a list of strings.")

    if len(set(left_ids)) != len(left_ids):
        raise ValueError("left_ids contains duplicates.")

    if len(set(right_ids)) != len(right_ids):
        raise ValueError("right_ids contains duplicates.")

    if not isinstance(weights, dict):
        raise ValueError("weights must be an object.")

    normalized: dict[str, dict[str, float]] = {}

    for left_id in left_ids:
        row = weights.get(left_id)

        if not isinstance(row, dict):
            raise ValueError(
                f"weights[{left_id!r}] must be an object."
            )

        normalized[left_id] = {}

        for right_id in right_ids:
            if right_id not in row:
                raise ValueError(
                    f"Missing weight for edge ({left_id}, {right_id})."
                )

            try:
                value = float(row[right_id])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Weight ({left_id}, {right_id}) is not numeric."
                ) from exc

            if not math.isfinite(value):
                raise ValueError(
                    f"Weight ({left_id}, {right_id}) must be finite."
                )

            normalized[left_id][right_id] = value

    return left_ids, right_ids, normalized


def solve_bipartite_matching(
    optimization_input: dict[str, Any],
) -> dict[str, Any]:
    """
    Deterministic Gurobi maximum-weight bipartite matching solver.

    The pipeline calls this function after generated aggregation code creates
    the optimization input.
    """

    left_ids, right_ids, weights = _validate_matching_input(
        optimization_input
    )

    positive_edges = [
        (left_id, right_id)
        for left_id in left_ids
        for right_id in right_ids
        if weights[left_id][right_id] > 0.0
    ]

    model = gp.Model("surveyopt_bipartite_matching")
    model.Params.OutputFlag = 0

    x = model.addVars(
        positive_edges,
        vtype=GRB.BINARY,
        name="match",
    )

    for left_id in left_ids:
        model.addConstr(
            gp.quicksum(
                x[left_id, right_id]
                for right_id in right_ids
                if (left_id, right_id) in x
            )
            <= 1,
            name=f"left_capacity[{left_id}]",
        )

    for right_id in right_ids:
        model.addConstr(
            gp.quicksum(
                x[left_id, right_id]
                for left_id in left_ids
                if (left_id, right_id) in x
            )
            <= 1,
            name=f"right_capacity[{right_id}]",
        )

    model.setObjective(
        gp.quicksum(
            weights[left_id][right_id] * x[left_id, right_id]
            for left_id, right_id in positive_edges
        ),
        GRB.MAXIMIZE,
    )

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(
            f"Gurobi did not find an optimal solution. "
            f"Status={model.Status}"
        )

    pairs: list[dict[str, Any]] = []

    for left_id, right_id in positive_edges:
        if x[left_id, right_id].X > 0.5:
            pairs.append(
                {
                    "left_id": left_id,
                    "right_id": right_id,
                    "weight": weights[left_id][right_id],
                }
            )

    return {
        "status": "optimal",
        "objective_value": float(model.ObjVal),
        "pairs": pairs,
    }