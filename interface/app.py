from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, render_template, request, send_from_directory

from surveyopt.json_tasks import JsonTaskRunner
from surveyopt.llm import LLMRouter, OpenAIChatLLM
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

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = BASE_DIR / "runs"

DEFAULT_USER_PROMPT = (
    "Construct scores for matching people to vacation rentals. "
    "Respect explicit dealbreakers, budget limits, and basic non-negotiables. "
    "Interpret semantically similar phrases as potentially compatible, but "
    "avoid inventing preferences not supported by the response. Favor "
    "mutually plausible matches and prefer strong fits over generic ones."
)


def load_house_inventory() -> list[dict[str, Any]]:
    with (DATA_DIR / "houses.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def summarize_house(house: dict[str, Any]) -> str:
    if house.get("summary") and str(house.get("summary")).strip():
        base_summary = str(house["summary"]).strip()
    else:
        base_summary = (
            f"This property is a {house.get('bedrooms')} bedroom, {house.get('bathrooms')} "
            f"bath {house.get('style', 'home')} in {house.get('city', 'the area')}."
        )

    neighborhood = house.get("neighborhood") or "the local area"
    city = house.get("city") or "the city"
    state = house.get("state") or ""
    location = f"{neighborhood}, {city}"
    if state:
        location = f"{location}, {state}"

    features = house.get("features") or house.get("tags") or []
    feature_text = ", ".join(str(feature) for feature in features) if features else "general amenities"

    description = house.get("description") or base_summary
    image_url = house.get("image_url") or ""

    return (
        f"House profile: {base_summary} "
        f"Address: {house.get('address', 'unknown address')}. "
        f"Location: {location}. "
        f"Price: ${house.get('price', 0):,}. "
        f"Bedrooms: {house.get('bedrooms', 'unknown')}; Bathrooms: {house.get('bathrooms', 'unknown')}; "
        f"Square footage: {house.get('sqft', 'unknown')} sq ft. "
        f"Style: {house.get('style', 'unknown')}. "
        f"Latitude: {house.get('lat', 'unknown')}; Longitude: {house.get('lng', 'unknown')}. "
        f"Features: {feature_text}. "
        f"Description: {description}. "
        f"Image URL: {image_url}."
    ).strip()


def create_pipeline() -> DecisionPipeline:
    api_key = os.getenv("PARLEY_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set PARLEY_API_KEY or OPENAI_API_KEY before running the app."
        )

    standard_llm = OpenAIChatLLM(
        api_key=api_key,
        base_url=os.getenv(
            "PARLEY_BASE_URL",
            "https://parley.api.mit.edu/v1",
        ),
        model="openai/gpt-5.4-nano",
    )

    smart_llm = OpenAIChatLLM(
        api_key=api_key,
        base_url=os.getenv(
            "PARLEY_BASE_URL",
            "https://parley.api.mit.edu/v1",
        ),
        model=os.getenv(
            "PARLEY_SMART_MODEL",
            "openai/gpt-5.6-terra",
        ),
    )

    return DecisionPipeline(
        task_runner=JsonTaskRunner(
            router=LLMRouter(
                standard=standard_llm,
                smart=smart_llm,
            ),
            max_attempts=2,
        ),
        config=PipelineConfig(
            use_meta_orchestrator=False,
            artifact_root=RUNS_DIR,
            response_sample_size=10,
            agent_workers=8,
            meta_idea_count=1,
            max_revision_rounds=3,
        ),
    )


def build_matching_payload(
    users: list[dict[str, str]],
    houses: list[dict[str, Any]],
    user_prompt: str | None = None,
) -> tuple[list[SurveyDefinition], list[SurveyResponse], DecisionProblem, DecisionGuidance]:
    user_survey = SurveyDefinition(
        id="user_home_preferences",
        respondent_type="user",
        questions=[
            SurveyQuestion(
                id="housing_preferences",
                text=(
                    "Describe what kind of home you want, along with must-haves, "
                    "nice-to-haves, and any dealbreakers."
                ),
            )
        ],
    )

    house_survey = SurveyDefinition(
        id="house_profile",
        respondent_type="house",
        questions=[
            SurveyQuestion(
                id="house_summary",
                text=(
                    "Provide a compact summary of the home, its features, and the "
                    "area it is in. Include all explicit structured details from the "
                    "listing, including the city, state, neighborhood, price, bedrooms, "
                    "bathrooms, square footage, home style, coordinates, image URL, "
                    "and list of amenities or features."
                ),
            )
        ],
    )

    responses: list[SurveyResponse] = []
    for user in users:
        responses.append(
            SurveyResponse(
                entity_id=user["id"],
                entity_type="user",
                survey_id="user_home_preferences",
                answers={
                    "housing_preferences": user["preferences"],
                },
            )
        )

    for house in houses:
        responses.append(
            SurveyResponse(
                entity_id=house["id"],
                entity_type="house",
                survey_id="house_profile",
                answers={
                    "house_summary": summarize_house(house),
                },
            )
        )

    decision_problem = DecisionProblem(
        name="maximum_weight_bipartite_matching",
        function=solve_bipartite_matching,
        documentation=BIPARTITE_MATCHING_DOCUMENTATION,
    )

    guidance = DecisionGuidance(
        user_prompt=(user_prompt or DEFAULT_USER_PROMPT).strip()
        or DEFAULT_USER_PROMPT,
    )

    return [user_survey, house_survey], responses, decision_problem, guidance


def parse_user_entries(form_data: dict[str, str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    index = 0

    while True:
        name_key = f"user_{index}_name"
        pref_key = f"user_{index}_preferences"
        name = (form_data.get(name_key) or "").strip()
        preferences = (form_data.get(pref_key) or "").strip()

        if not name and not preferences:
            break

        if not name:
            name = f"User {index + 1}"

        if not preferences:
            preferences = (
               "I want a clean, comfortable vacation house in a quiet area with a realistic budget of about $250–$400 per night, plus a well-equipped kitchen, reliable Wi-Fi, and enough bedrooms for my group."
            )

        entries.append(
            {
                "id": f"user_{index + 1}",
                "name": name,
                "preferences": preferences,
            }
        )
        index += 1

    if not entries:
        entries = [
            {
                "id": "user_1",
                "name": "User 1",
                "preferences": (
                    "I want a private vacation home near beaches, hiking trails, or local attractions, with outdoor space such as a patio, deck, pool, or fire pit, while keeping the total nightly cost under about $500."
                ),
            }
        ]

    return entries


def get_house_match_map(decision: dict[str, Any]) -> dict[str, str]:
    pairs = decision.get("pairs", []) if isinstance(decision, dict) else []
    match_map: dict[str, str] = {}
    for pair in pairs:
        left_id = pair.get("left_id")
        right_id = pair.get("right_id")
        if left_id and right_id:
            match_map[str(left_id)] = str(right_id)
    return match_map


def build_run_artifact_links(run_directory: Path) -> dict[str, str]:
    run_id = run_directory.name
    candidate_dir = run_directory / "candidates"
    if not candidate_dir.exists():
        return {
            "run_summary": f"/runs/{run_id}/run_summary.json",
        }

    candidate_roots = sorted(candidate_dir.iterdir())
    if not candidate_roots:
        return {
            "run_summary": f"/runs/{run_id}/run_summary.json",
        }

    first_candidate = candidate_roots[0]
    round_roots = sorted(first_candidate.glob("round_*"))
    if not round_roots:
        return {
            "run_summary": f"/runs/{run_id}/run_summary.json",
        }

    first_round = round_roots[-1]
    candidate_name = first_candidate.name
    round_name = first_round.name

    return {
        "run_summary": f"/runs/{run_id}/run_summary.json",
        "question_agent_plan": (
            f"/runs/{run_id}/candidates/{candidate_name}/{round_name}/"
            "question_agent_plan_output.json"
        ),
        "aggregation_code": (
            f"/runs/{run_id}/candidates/{candidate_name}/{round_name}/"
            "aggregation_code.py"
        ),
        "aggregation_output": (
            f"/runs/{run_id}/candidates/{candidate_name}/{round_name}/"
            "aggregation_code_output.json"
        ),
        "agent_outputs": (
            f"/runs/{run_id}/candidates/{candidate_name}/{round_name}/agent_outputs"
        ),
    }


app = Flask(__name__)


@app.get("/")
def index() -> str:
    houses = load_house_inventory()
    default_users = [
        {
            "id": "user_1",
            "name": "User 1",
            "preferences": (
                "I want a distinctive and relaxing getaway with beautiful views, comfortable common areas, and convenient amenities like parking, laundry, and air conditioning, ideally within a $150–$300 per-night budget."
            ),
        },
        {
            "id": "user_2",
            "name": "User 2",
            "preferences": (
                "I want a private vacation home near beaches, hiking trails, or local attractions, with outdoor space such as a patio, deck, pool, or fire pit, while keeping the total nightly cost under about $500."
            ),
        },
        {
            "id": "user_3",
            "name": "User 3",
            "preferences": (
                "I want a clean, comfortable vacation house in a quiet area with a realistic budget of about $250–$400 per night, plus a well-equipped kitchen, reliable Wi-Fi, and enough bedrooms for my group."
            ),
        },
    ]
    return render_template(
        "index.html",
        houses=houses,
        default_users=default_users,
        default_user_prompt=DEFAULT_USER_PROMPT,
    )


@app.post("/match")
def match_houses():
    users = parse_user_entries(request.form)
    houses = load_house_inventory()
    user_prompt = (request.form.get("user_prompt") or DEFAULT_USER_PROMPT).strip()

    try:
        surveys, responses, decision_problem, guidance = build_matching_payload(
            users=users,
            houses=houses,
            user_prompt=user_prompt,
        )

        pipeline = create_pipeline()
        successful_results = pipeline.run(
            surveys=surveys,
            responses=responses,
            decision_problem=decision_problem,
            guidance=guidance,
        )

        if not successful_results:
            return render_template(
                "results.html",
                users=users,
                houses=houses,
                matched_houses=[],
                run_id=None,
                run_summary_url=None,
                artifacts={},
                errors=[
                    "No feasible match was approved by the audit step. Try widening the criteria or editing the preferences."
                ],
            )

        result = successful_results[0]
        decision = result.decision or {}
        match_map = get_house_match_map(decision)

        matched_houses = []
        house_lookup = {house["id"]: house for house in houses}
        for user in users:
            house_id = match_map.get(user["id"])
            if not house_id:
                matched_houses.append(
                    {
                        "user": user,
                        "house": None,
                        "reason": "No strong match was selected for this user.",
                    }
                )
                continue

            house = house_lookup.get(house_id)
            if house is None:
                matched_houses.append(
                    {
                        "user": user,
                        "house": None,
                        "reason": "Matched house record not found.",
                    }
                )
                continue

            matched_houses.append(
                {
                    "user": user,
                    "house": house,
                    "reason": "Preferred fit generated by the matching pipeline.",
                }
            )

        run_id = result.run_directory.name
        run_summary_url = f"/runs/{run_id}/run_summary.json"
        artifacts = build_run_artifact_links(result.run_directory)
        return render_template(
            "results.html",
            users=users,
            houses=houses,
            matched_houses=matched_houses,
            run_id=run_id,
            run_summary_url=run_summary_url,
            artifacts=artifacts,
            decision=decision,
        )
    except Exception as exc:
        return render_template(
            "results.html",
            users=users,
            houses=houses,
            matched_houses=[],
            run_id=None,
            run_summary_url=None,
            artifacts={},
            errors=[
                f"Matching failed: {exc}",
                "Set PARLEY_API_KEY or OPENAI_API_KEY before submitting the form.",
            ],
        )


@app.get("/runs")
def list_runs():
    run_dirs = []
    for path in sorted(RUNS_DIR.iterdir(), reverse=True):
        if path.is_dir():
            run_dirs.append(path.name)
    return render_template("run_directory.html", directory_name="runs", entries=run_dirs, is_root=True)


@app.get("/runs/<path:filename>")
def serve_run_file(filename: str):
    full_path = RUNS_DIR / filename
    if full_path.is_dir():
        entries = []
        for child in sorted(full_path.iterdir()):
            entries.append({
                "name": child.name,
                "path": f"/runs/{filename}/{child.name}",
                "is_dir": child.is_dir(),
            })
        return render_template(
            "run_directory.html",
            directory_name=filename,
            entries=entries,
            is_root=False,
        )
    return send_from_directory(str(RUNS_DIR), filename)


if __name__ == "__main__":
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
