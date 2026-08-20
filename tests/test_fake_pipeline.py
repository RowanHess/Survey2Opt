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


class RecordingTextFixtureLLM(TextFixtureLLM):
    def __init__(self, fixture_directory: Path) -> None:
        super().__init__(fixture_directory)
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return super().complete(request)


AGGREGATION_CODE = """
def aggregate(question_outputs, survey, responses):
    left = {}
    right = {}

    for entry in question_outputs:
        entity_type = entry["entity_type"]
        entity_id = entry["entity_id"]
        output = entry.get("output", {})
        categories = output.get("categories", [])

        if entity_type == "seeker":
            left[entity_id] = categories

        if entity_type == "candidate":
            right[entity_id] = categories

    weights = {}

    for left_id in left:
        row = {}

        for right_id in right:
            score = 0

            for category in left.get(left_id, []):
                if category in right.get(right_id, []):
                    score = 1

            row[right_id] = score

        weights[left_id] = row

    return {
        "left_ids": list(left),
        "right_ids": list(right),
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

    question_agent_plan = {
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
        "assumptions": [
            "A shared category indicates compatibility."
        ],
        "representation_summary": "Normalize answers into categories.",
    }

    write_fixture(
        fixture_directory,
        "tone_calibrator",
        {
            "profiles": [
                {
                    "entity_id": "seeker_1",
                    "entity_type": "seeker",
                    "verbosity": "medium",
                    "directness": "medium",
                    "emphasis": "low",
                    "hedging": "medium",
                    "confidence": "low",
                    "style_summary": "Limited evidence; generally neutral.",
                },
                {
                    "entity_id": "candidate_1",
                    "entity_type": "candidate",
                    "verbosity": "low",
                    "directness": "medium",
                    "emphasis": "low",
                    "hedging": "low",
                    "confidence": "medium",
                    "style_summary": "Usually calm and concise.",
                },
                {
                    "entity_id": "candidate_2",
                    "entity_type": "candidate",
                    "verbosity": "low",
                    "directness": "high",
                    "emphasis": "high",
                    "hedging": "low",
                    "confidence": "medium",
                    "style_summary": "Usually concise and emphatic.",
                },
            ]
        },
    )

    write_fixture(
        fixture_directory,
        "question_format_orchestrator__direct_orchestration__round_1",
        question_agent_plan,
    )

    write_fixture(
        fixture_directory,
        "aggregation_code_orchestrator__direct_orchestration__round_1",
        {
            "code": AGGREGATION_CODE,
            "rationale": (
                "Use binary overlap between desired and available categories."
            ),
        },
    )

    write_fixture(
        fixture_directory,
        (
            "direct_orchestration__round_1__seeker_categories"
            "__seeker_survey__desired_partner"
        ),
        {
            "outputs": {
                "seeker_1": {"categories": ["hiking", "dogs"]},
            }
        },
    )

    write_fixture(
        fixture_directory,
        (
            "direct_orchestration__round_1__candidate_categories"
            "__candidate_survey__self_description"
        ),
        {
            "outputs": {
                "candidate_1": {"categories": ["hiking", "dogs"]},
                "candidate_2": {"categories": ["museums"]},
            }
        },
    )

    write_fixture(
        fixture_directory,
        "auditor__direct_orchestration__round_1",
        {
            "approved": True,
            "summary": "The test decision is reasonable.",
            "issues": [],
            "feedback_to_orchestrator": "",
        },
    )

    fake_llm = RecordingTextFixtureLLM(fixture_directory)

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
            use_meta_orchestrator=False,
            max_revision_rounds=1,
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
            ),
            SurveyQuestion(
                id="priority_context",
                text="Describe how strongly you usually state preferences.",
            ),
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
                "self_description": "I have a dog and hike often.",
                "priority_context": "I usually describe things calmly.",
            },
        ),
        SurveyResponse(
            entity_id="candidate_2",
            entity_type="candidate",
            survey_id="candidate_survey",
            answers={
                "self_description": "I enjoy art museums.",
                "priority_context": "I tend to use emphatic language.",
            },
        ),
    ]

    successful_results = pipeline.run(
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

    assert len(successful_results) == 1

    result = successful_results[0]
    final_round = result.rounds[-1]
    assert final_round.optimization_input is not None
    weights = final_round.optimization_input["weights"]

    assert weights["seeker_1"]["candidate_1"] == 1
    assert weights["seeker_1"]["candidate_2"] == 0

    assert (result.run_directory / "inputs.json").exists()
    assert (result.run_directory / "tone_profiles.json").exists()
    assert (result.run_directory / "run_summary.json").exists()

    round_directory = result.candidate_directory / "round_01"
    assert (round_directory / "question_agent_plan_output.json").exists()
    assert (round_directory / "optimization_input.json").exists()
    assert (round_directory / "decision.json").exists()

    agent_files = list(
        (round_directory / "agent_outputs").glob("*.json")
    )

    # One LLM call/artifact per survey question, not per respondent answer.
    assert len(agent_files) == 2

    candidate_batch = next(
        path for path in agent_files
        if "candidate_categories" in path.name
    )
    candidate_artifact = json.loads(
        candidate_batch.read_text(encoding="utf-8")
    )
    assert candidate_artifact["respondent_count"] == 2
    assert len(candidate_artifact["outputs"]) == 2

    question_agent_requests = [
        request
        for request in fake_llm.requests
        if request.task_id.startswith("direct_orchestration__round_1__")
    ]
    assert len(question_agent_requests) == 2

    candidate_request = next(
        request
        for request in question_agent_requests
        if "candidate_categories" in request.task_id
    )
    assert "candidate_1" in candidate_request.user_prompt
    assert "candidate_2" in candidate_request.user_prompt
    assert "Never score or rank a respondent" in (
        candidate_request.system_prompt
    )
    assert "verbosity" in candidate_request.system_prompt
    assert "within-person tone calibration" in candidate_request.user_prompt
    assert "Usually calm and concise." in candidate_request.user_prompt
    assert "Usually concise and emphatic." in candidate_request.user_prompt
    assert "I usually describe things calmly." not in candidate_request.user_prompt
    assert "I tend to use emphatic language." not in candidate_request.user_prompt

    calibration_requests = [
        request
        for request in fake_llm.requests
        if request.task_id == "tone_calibrator"
    ]
    assert len(calibration_requests) == 1
    assert "I usually describe things calmly." in (
        calibration_requests[0].user_prompt
    )
    assert "I tend to use emphatic language." in (
        calibration_requests[0].user_prompt
    )
