from __future__ import annotations

import pytest

from surveyopt.matching import solve_bipartite_matching


def test_bipartite_matching() -> None:
    #pytest.importorskip("gurobipy")

    optimization_input = {
        "left_ids": ["a", "b"],
        "right_ids": ["x", "y"],
        "weights": {
            "a": {
                "x": 10.0,
                "y": 1.0,
            },
            "b": {
                "x": 9.0,
                "y": 8.0,
            },
        },
    }

    try:
        result = solve_bipartite_matching(optimization_input)
    except Exception as exc:        
        # pytest.skip(
        #     f"Gurobi is unavailable or unlicensed in this environment: {exc}"
        # )
        pass

    assert result["status"] == "optimal"
    assert result["objective_value"] == 18.0

    pairs = {
        (pair["left_id"], pair["right_id"])
        for pair in result["pairs"]
    }

    assert pairs == {
        ("a", "x"),
        ("b", "y"),
    }