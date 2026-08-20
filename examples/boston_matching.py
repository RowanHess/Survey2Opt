#!/usr/bin/env python3
"""Run Survey2Opt matching on the Boston house_data + person survey set."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surveyopt.json_tasks import JsonTaskRunner
from surveyopt.llm import LLMRouter, OpenAIChatLLM
from surveyopt.matching import (
    BIPARTITE_MATCHING_DOCUMENTATION,
    solve_bipartite_matching,
)
from surveyopt.models import DecisionProblem
from surveyopt.pipeline import DecisionPipeline, PipelineConfig

from data.boston_housing import (
    all_responses,
    boston_guidance,
    dataset_summary,
    house_survey,
    person_survey,
)


def main() -> None:
    print("Dataset:", json.dumps(dataset_summary(), indent=2))

    standard_llm = OpenAIChatLLM(
        api_key=os.environ["PARLEY_API_KEY"],
        base_url=os.getenv(
            "PARLEY_BASE_URL",
            "https://parley.api.mit.edu/v1",
        ),
        model=os.getenv("PARLEY_STANDARD_MODEL", "openai/gpt-5.4-nano"),
    )
    smart_llm = OpenAIChatLLM(
        api_key=os.environ["PARLEY_API_KEY"],
        base_url=os.getenv(
            "PARLEY_BASE_URL",
            "https://parley.api.mit.edu/v1",
        ),
        model=os.getenv("PARLEY_SMART_MODEL", "openai/gpt-5.6-terra"),
    )

    pipeline = DecisionPipeline(
        task_runner=JsonTaskRunner(
            router=LLMRouter(standard=standard_llm, smart=smart_llm),
            max_attempts=2,
        ),
        config=PipelineConfig(
            artifact_root="runs",
            response_sample_size=8,
            agent_workers=8,
            meta_idea_count=1,
            max_revision_rounds=3,
            use_meta_orchestrator=False,
        ),
    )

    decision_problem = DecisionProblem(
        name="maximum_weight_bipartite_matching",
        function=solve_bipartite_matching,
        documentation=BIPARTITE_MATCHING_DOCUMENTATION,
    )

    successful_results = pipeline.run(
        surveys=[house_survey, person_survey],
        responses=all_responses,
        decision_problem=decision_problem,
        guidance=boston_guidance,
    )

    if not successful_results:
        print(
            "No candidate strategy was approved by the auditor. "
            "Inspect the run artifacts for rejected strategies and feedback."
        )
        return

    print(f"{len(successful_results)} strategy or strategies were approved.")
    for result in successful_results:
        print()
        print(f"Strategy ID: {result.strategy.id}")
        print(f"Strategy title: {result.strategy.title}")
        print(f"Artifacts: {result.candidate_directory}")
        print("Decision:")
        print(json.dumps(result.decision, indent=2))


if __name__ == "__main__":
    main()
