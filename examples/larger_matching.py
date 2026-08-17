from __future__ import annotations

import json
import os

from surveyopt.llm import LLMRouter, OpenAIChatLLM
from surveyopt.json_tasks import JsonTaskRunner
from surveyopt.matching import (
    BIPARTITE_MATCHING_DOCUMENTATION,
    solve_bipartite_matching,
)
from surveyopt.models import (
    DecisionGuidance,
    DecisionProblem,
    SurveyDefinition,
    SurveyQuestion,
    SurveyResponse,
)
from surveyopt.pipeline import DecisionPipeline, PipelineConfig

from larger_data import house_survey, person_survey, load_survey_responses, house_responses


def main() -> None:
    standard_llm = OpenAIChatLLM(
        api_key=os.environ["PARLEY_API_KEY"],
        base_url=os.getenv(
            "PARLEY_BASE_URL",
            "https://parley.api.mit.edu/v1",
        ),
        model="openai/gpt-5.4-nano",
        #default_temperature=0.0,
    )

    # This may be the same model initially. Later, replace it with a stronger
    # model for JSON repair and other high-stakes steps.
    smart_llm = OpenAIChatLLM(
        api_key=os.environ["PARLEY_API_KEY"],
        base_url=os.getenv(
            "PARLEY_BASE_URL",
            "https://parley.api.mit.edu/v1",
        ),
        model=os.getenv(
            "PARLEY_SMART_MODEL",
            "openai/gpt-5.6-terra",
        ),
        #default_temperature=0.0,
    )

    pipeline = DecisionPipeline(
        task_runner=JsonTaskRunner(
            router=LLMRouter(
                standard=standard_llm,
                smart=smart_llm,
            ),
            max_attempts=2,
        ),
        config=PipelineConfig(
            artifact_root="runs",
            response_sample_size=2,
            agent_workers=8,
            meta_idea_count=1,
            max_revision_rounds=3,
            use_meta_orchestrator=False,
        ),
    )


    responses = house_responses + load_survey_responses('examples/person_survey_responses.json')

    #print(responses[-1])

    decision_problem = DecisionProblem(
        name="maximum_weight_bipartite_matching",
        function=solve_bipartite_matching,
        documentation=BIPARTITE_MATCHING_DOCUMENTATION,
    )

    guidance = DecisionGuidance(
        user_prompt=(
            "Construct a matching between people and houses. Pay attention to"
            "hard constraints, such fitting a large family in a small house and budget."
            "Beyond that, try to make people happy and put them in places where they are employable."
            "Avoid leaving houses unmatched. No more than a few houses should be unmatched."
            "Create a process that avoids placing weight 0 on edges unless there is real incompatability, not merely a preference."
        )
    )


    successful_results = pipeline.run(
        surveys=[
            house_survey,
            person_survey,
        ],
        responses=responses,
        decision_problem=decision_problem,
        guidance=guidance,
    )

    if not successful_results:
        print(
            "No candidate strategy was approved by the auditor. "
            "Inspect the run artifacts for rejected strategies and feedback."
        )
    else:
        print(
            f"{len(successful_results)} strategy or strategies "
            "were approved."
        )

        for result in successful_results:
            print()
            print(f"Strategy ID: {result.strategy.id}")
            print(f"Strategy title: {result.strategy.title}")
            print(f"Artifacts: {result.candidate_directory}")
            print("Decision:")
            print(json.dumps(result.decision, indent=2))



if __name__ == "__main__":
    main()