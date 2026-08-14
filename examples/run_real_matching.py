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
            response_sample_size=10,
            agent_workers=8,
            meta_idea_count=1,
            max_revision_rounds=3,
        ),
    )

    seeker_survey = SurveyDefinition(
        id="seeker_survey",
        respondent_type="seeker",
        questions=[
            SurveyQuestion(
                id="desired_partner",
                text=(
                    "Describe traits, interests, preferences, and dealbreakers "
                    "you want in a potential match."
                ),
            ),
        ],
    )

    candidate_survey = SurveyDefinition(
        id="candidate_survey",
        respondent_type="candidate",
        questions=[
            SurveyQuestion(
                id="self_description",
                text=(
                    "Describe your interests, lifestyle, values, and relevant "
                    "personal attributes."
                ),
            ),
        ],
    )

    responses = [
        SurveyResponse(
            entity_id="seeker_ada",
            entity_type="seeker",
            survey_id="seeker_survey",
            answers={
                "desired_partner": (
                    "I value spontaneity, kindness, people who enjoy hiking, "
                    "and someone who likes dogs. I cannot live with cats "
                    "because of an allergy."
                )
            },
        ),
        SurveyResponse(
            entity_id="seeker_ben",
            entity_type="seeker",
            survey_id="seeker_survey",
            answers={
                "desired_partner": (
                    "I prefer someone who enjoys museums, cooking, and quiet "
                    "weekends."
                )
            },
        ),
        SurveyResponse(
            entity_id="candidate_cara",
            entity_type="candidate",
            survey_id="candidate_survey",
            answers={
                "self_description": (
                    "I have a dog, hike most weekends, enjoy spontaneous "
                    "road trips, and work in conservation."
                )
            },
        ),
        SurveyResponse(
            entity_id="candidate_dan",
            entity_type="candidate",
            survey_id="candidate_survey",
            answers={
                "self_description": (
                    "I like cooking elaborate meals, visiting art museums, "
                    "and having calm weekends at home."
                )
            },
        ),
    ]

    decision_problem = DecisionProblem(
        name="maximum_weight_bipartite_matching",
        function=solve_bipartite_matching,
        documentation=BIPARTITE_MATCHING_DOCUMENTATION,
    )

    guidance = DecisionGuidance(
        user_prompt=(
            "Construct compatibility scores for a dating application. "
            "Respect explicit dealbreakers. Interpret semantically similar "
            "phrases as potentially compatible, but avoid inventing "
            "preferences not supported by a response. The matching should "
            "favor mutually plausible matches."
        )
    )

    successful_results = pipeline.run(
        surveys=[
            seeker_survey,
            candidate_survey,
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