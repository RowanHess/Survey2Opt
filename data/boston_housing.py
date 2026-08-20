"""Greater Boston housing + person survey data for matching and tone ablations.

Houses: `data/house_data.py` (City of Boston assessment/sales–grounded listings)
People: `data/person_survey_responses.json`
Tone packs: `data/tone_ablations.json` (soft / neutral / harsh)

    from data.boston_housing import (
        house_survey,
        person_survey,
        house_responses,
        person_responses,
        all_responses,
        boston_guidance,
        load_tone_ablation_responses,
    )
"""

from __future__ import annotations

import json
from pathlib import Path

from surveyopt.models import (
    DecisionGuidance,
    SurveyDefinition,
    SurveyQuestion,
    SurveyResponse,
)

from data.house_data import house_responses, house_survey

_DATA_ROOT = Path(__file__).resolve().parent

person_survey = SurveyDefinition(
    id="person_survey",
    respondent_type="person",
    questions=[
        SurveyQuestion(
            id="personal_context",
            text=(
                "Describe your household and lifestyle, including household members, "
                "children, pets, work arrangement, relocation flexibility, and important "
                "daily-life constraints."
            ),
        ),
        SurveyQuestion(
            id="budget",
            text=(
                "Describe your housing budget, including maximum comfortable purchase "
                "price, maximum monthly housing cost, importance of affordability, "
                "renovation tolerance, and tolerance for ongoing maintenance."
            ),
        ),
        SurveyQuestion(
            id="housing_preferences",
            text=(
                "Describe your preferred physical house, including bedrooms, bathrooms, "
                "property type, size, parking, outdoor space, condition, storage, "
                "accessibility, and need for a dedicated office."
            ),
        ),
        SurveyQuestion(
            id="location_and_transportation",
            text=(
                "Describe your preferred location and transportation situation, including "
                "urbanicity, walkability, public transportation, car access, commute "
                "tolerance, proximity to major cities, noise, and privacy."
            ),
        ),
        SurveyQuestion(
            id="climate_and_environment",
            text=(
                "Describe your climate and environmental preferences, including tolerance "
                "for cold, snow, heat, humidity, drought, wildfire smoke, flooding, "
                "severe storms, and preferred access to nature or outdoor recreation."
            ),
        ),
        SurveyQuestion(
            id="amenities_and_services",
            text=(
                "Describe the nearby amenities and services you need, including groceries, "
                "restaurants, healthcare, schools, childcare, libraries, education, "
                "parks, culture, and preferred travel times."
            ),
        ),
        SurveyQuestion(
            id="community_jobs_and_priorities",
            text=(
                "Describe your preferred community, culture, and employment environment. "
                "Include diversity, social activity, newcomer friendliness, local culture, "
                "industries and occupations you need nearby, remote-work needs, your top "
                "housing priorities and important tradeoffs."
            ),
        ),
    ],
)


def _responses_from_raw(raw: list[dict]) -> list[SurveyResponse]:
    return [
        SurveyResponse(
            entity_id=str(item["entity_id"]),
            entity_type=str(item["entity_type"]),
            survey_id=str(item["survey_id"]),
            answers=dict(item["answers"]),
        )
        for item in raw
    ]


def load_person_responses(
    json_path: str | Path | None = None,
) -> list[SurveyResponse]:
    path = Path(json_path) if json_path else (
        _DATA_ROOT / "person_survey_responses.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload["responses"] if isinstance(payload, dict) else payload
    return _responses_from_raw(raw)


def load_tone_ablation_responses(
    condition: str,
    json_path: str | Path | None = None,
) -> list[SurveyResponse]:
    """Load person responses for one tone condition: soft | neutral | harsh."""
    path = Path(json_path) if json_path else (_DATA_ROOT / "tone_ablations.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    variants = payload.get("variants") or {}
    if condition not in variants:
        raise KeyError(
            f"Unknown tone condition {condition!r}. "
            f"Available: {sorted(variants)}"
        )
    return _responses_from_raw(variants[condition])


person_responses = load_person_responses()
all_responses = list(house_responses) + list(person_responses)

boston_guidance = DecisionGuidance(
    user_prompt=(
        "Match people to Greater Boston houses. Respect hard constraints such as "
        "budget ceilings, bedroom needs for household size, parking when a car is "
        "required, and accessibility when relevant. Prefer placements where people "
        "can reasonably live and work. Avoid zero-weight edges unless there is a "
        "real incompatibility, not merely a soft preference. Try not to leave many "
        "houses unmatched."
    )
)


def dataset_summary() -> dict[str, int | str]:
    return {
        "n_houses": len(house_responses),
        "n_people": len(person_responses),
        "n_responses": len(all_responses),
        "house_survey_id": house_survey.id,
        "person_survey_id": person_survey.id,
        "house_source": str(_DATA_ROOT / "house_data.py"),
        "person_source": str(_DATA_ROOT / "person_survey_responses.json"),
        "tone_ablations_source": str(_DATA_ROOT / "tone_ablations.json"),
    }


__all__ = [
    "house_survey",
    "person_survey",
    "house_responses",
    "person_responses",
    "all_responses",
    "boston_guidance",
    "load_person_responses",
    "load_tone_ablation_responses",
    "dataset_summary",
]
