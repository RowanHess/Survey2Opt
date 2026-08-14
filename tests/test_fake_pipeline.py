from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from surveyopt.json_tasks import JsonTaskRunner
from surveyopt.llm import LLMRouter, TextFixtureLLM
from surveyopt.models import (
    DecisionGuidance,
    DecisionProblem,
    SurveyDefinition,
    SurveyQuestion,
    SurveyResponse,
)
from surveyopt.pipeline import DecisionPipeline, PipelineConfig


CATEGORY_SCHEMA = {
    "type": "object",
    "required": ["categories"],
    "properties": {
        "categories": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "additionalProperties": False,
}


AGGREGATION_CODE = """
def aggregate(question_outputs, survey, responses):
    left = {}
    right = {}

    for entry in question_outputs:
        entity_type = get(entry, "entity_type")
        entity_id = get(entry, "entity_id")
        output = get(entry, "output", {})
        categories = get(output, "categories", [])

        if entity_type == "seeker":
            set_item(left, entity_id, categories)

        if entity_type == "candidate":
            set_item(right, entity_id, categories)

    weights = {}

    for left_id in keys(left):
        row = {}

        for right_id in keys(right):
            score = 0

            for category in get(left, left_id, []):
                if category in get(right, right_id, []):
                    score = 1

            set_item(row, right_id, score)

        set_item(weights, left_id, row)

    return {
        "left_ids": keys(left),
        "right_ids": keys(right),
        "weights": weights
    }
""".strip()


def fake_solver(
    optimization_input: dict[str, Any],
) -> dict[str, Any]:
    """
    Used only in this no-Gurobi pipeline test.

    The production example uses solve_bipartite_matching instead.
    """

    total = sum(
        score
        for row in optimization_input["weights"].values()
        for score in row.values()
    )

    return {
        "status": "test",
        "objective_value": total,
        "pairs": [],
    }


def write_fixture(
    fixture_directory: Path,
    name: str,
    value: dict[str, Any],
) -> None:
    (fixture_directory / f"{name}.txt").write_text(
        json.dumps(value),
        encoding="utf-8",
    )


def test_fake_pipeline(tmp_path: Path) -> None:
    fixture_directory = tmp_path / "fixtures"
    fixture_directory.mkdir()

    orchestrator_plan = {
        "question_tasks": [
            {
                "task_id": "seeker_categories",
                "kind": "question",
                "system_prompt": (
                    "You extract normalized preference categories."
                ),
                "instructions": (
                    "Return categories desired by the seeker."
                ),
                "target_entity_type": "seeker",
                "target_question_id": "desired_partner",
                "output_schema": CATEGORY_SCHEMA,
            },
            {
                "task_id": "candidate_categories",
                "kind": "question",
                "system_prompt": (
                    "You extract normalized attribute categories."
                ),
                "instructions": (
                    "Return categories possessed by the candidate."
                ),
                "target_entity_type": "candidate",
                "target_question_id": "self_description",
                "output_schema": CATEGORY_SCHEMA,
            },
        ],
        "aggregation": {
            "code": AGGREGATION_CODE,
            "rationale": (
                "Use binary overlap between desired and available categories."
            ),
        },
        "assumptions": [
            "A shared category indicates compatibility."
        ],
    }

    write_fixture(
        fixture_directory,
        "orchestrator",
        orchestrator_plan,
    )

    write_fixture(
        fixture_directory,
        "seeker_categories__seeker_1__desired_partner",
        {"categories": ["hiking", "dogs"]},
    )

    write_fixture(
        fixture_directory,
        "candidate_categories__candidate_1__self_description",
        {"categories": ["hiking", "dogs"]},
    )

    write_fixture(
        fixture_directory,
        "candidate_categories__candidate_2__self_description",
        {"categories": ["museums"]},
    )

    fake_llm = TextFixtureLLM(fixture_directory)

    pipeline = DecisionPipeline(
        task_runner=JsonTaskRunner(
            router=LLMRouter(
                standard=fake_llm,
                smart=fake_llm,
            ),
            max_attempts=2,
        ),
        config=PipelineConfig(
            artifact_root=tmp_path / "runs",
            agent_workers=2,
        ),
    )

    seeker_survey = SurveyDefinition(
        id="seeker_survey",
        respondent_type="seeker",
        questions=[
            SurveyQuestion(
                id="desired_partner",
                text="Describe your ideal partner.",
            )
        ],
    )

    candidate_survey = SurveyDefinition(
        id="candidate_survey",
        respondent_type="candidate",
        questions=[
            SurveyQuestion(
                id="self_description",
                text="Describe yourself.",
            )
        ],
    )

    responses = [
        SurveyResponse(
            entity_id="seeker_1",
            entity_type="seeker",
            survey_id="seeker_survey",
            answers={
                "desired_partner": "I want someone who hikes and likes dogs."
            },
        ),
        SurveyResponse(
            entity_id="candidate_1",
            entity_type="candidate",
            survey_id="candidate_survey",
            answers={
                "self_description": "I have a dog and hike often."
            },
        ),
        SurveyResponse(
            entity_id="candidate_2",
            entity_type="candidate",
            survey_id="candidate_survey",
            answers={
                "self_description": "I enjoy art museums."
            },
        ),
    ]

    result = pipeline.run(
        surveys=[
            seeker_survey,
            candidate_survey,
        ],
        responses=responses,
        decision_problem=DecisionProblem(
            name="test_problem",
            function=fake_solver,
            documentation="Return a test optimization object.",
        ),
        guidance=DecisionGuidance(
            user_prompt="Build reasonable compatibility scores."
        ),
    )

    weights = result.optimization_input["weights"]

    assert weights["seeker_1"]["candidate_1"] == 1
    assert weights["seeker_1"]["candidate_2"] == 0

    assert (result.run_directory / "inputs.json").exists()
    assert (result.run_directory / "orchestrator_output.json").exists()
    assert (result.run_directory / "optimization_input.json").exists()
    assert (result.run_directory / "decision.json").exists()

    agent_files = list(
        (result.run_directory / "agent_outputs").glob("*.json")
    )

    assert len(agent_files) == 3