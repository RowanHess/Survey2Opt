
from surveyopt.models import (
    DecisionGuidance,
    DecisionProblem,
    SurveyDefinition,
    SurveyQuestion,
    SurveyResponse,
)

import json
import os
from pathlib import Path
from typing import Any

house_survey = SurveyDefinition(
    id="house_survey",
    respondent_type="house",
    questions=[
        SurveyQuestion(
            id="location_and_transportation",
            text=(
                "Describe the house's location, including city, state, region, "
                "urbanicity, walkability, public transportation, car dependence, "
                "distance to a major city, noise, and privacy."
            ),
        ),
        SurveyQuestion(
            id="cost_and_property",
            text=(
                "Describe the property's cost and physical characteristics, including "
                "purchase price, estimated monthly housing cost, property type, year "
                "built, square footage, lot size, bedrooms, bathrooms, parking, and "
                "outdoor space."
            ),
        ),
        SurveyQuestion(
            id="condition_and_features",
            text=(
                "Describe the house's condition and features, including renovation "
                "needs, expected maintenance, heating, cooling, energy efficiency, "
                "internet quality, storage, accessibility, and suitability for remote work."
            ),
        ),
        SurveyQuestion(
            id="amenities_and_services",
            text=(
                "Describe nearby amenities and services, including grocery stores, "
                "restaurants, healthcare, schools, libraries, colleges, trade schools, "
                "parks, and typical travel times."
            ),
        ),
        SurveyQuestion(
            id="climate_and_environment",
            text=(
                "Describe the climate and environment, including seasonal weather, "
                "typical temperatures, snow, humidity, natural scenery, outdoor "
                "recreation, and relevant natural hazards."
            ),
        ),
        SurveyQuestion(
            id="community_and_culture",
            text=(
                "Describe the local community and culture, including diversity, "
                "social atmosphere, recreation, entertainment, arts, community life, "
                "newcomer friendliness, and the general feel of the area."
            ),
        ),
        SurveyQuestion(
            id="jobs_and_tradeoffs",
            text=(
                "Describe the local economy and employment opportunities, including "
                "industries and occupations in demand, opportunities without a "
                "four-year degree, major employers, remote-work suitability, and the "
                "main advantages and disadvantages of living in this house and location."
            ),
        ),
    ],
)

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
                "housing priorities, dealbreakers, and important tradeoffs."
            ),
        ),
    ],
)


def load_survey_responses(
    json_path: str | Path,
) -> list[SurveyResponse]:
    """
    Load SurveyResponse objects from a JSON file.

    Supports the wrapped format produced by the generation code:

    {
        "survey_id": "person_survey",
        "respondent_type": "person",
        "people": [...],
        "responses": [...]
    }
    """

    json_path = Path(json_path)

    with json_path.open("r", encoding="utf-8") as file:
        data: Any = json.load(file)

    # The generated file stores responses under the "responses" key.
    if isinstance(data, dict):
        raw_responses = data.get("responses")

        if raw_responses is None:
            raise ValueError(
                f"JSON file {json_path} does not contain a 'responses' key."
            )

    # Also support a file containing a bare list of response dictionaries.
    elif isinstance(data, list):
        raw_responses = data

    else:
        raise ValueError(
            "Expected the JSON file to contain either an object or a list."
        )

    if not isinstance(raw_responses, list):
        raise ValueError("'responses' must be a list.")

    responses: list[SurveyResponse] = []

    for index, raw_response in enumerate(raw_responses):
        if not isinstance(raw_response, dict):
            raise ValueError(
                f"Response at index {index} is not a JSON object."
            )

        required_fields = {
            "entity_id",
            "entity_type",
            "survey_id",
            "answers",
        }

        missing_fields = required_fields - raw_response.keys()

        if missing_fields:
            raise ValueError(
                f"Response at index {index} is missing fields: "
                f"{sorted(missing_fields)}"
            )

        if not isinstance(raw_response["answers"], dict):
            raise ValueError(
                f"'answers' for response at index {index} must be a dictionary."
            )

        responses.append(
            SurveyResponse(
                entity_id=str(raw_response["entity_id"]),
                entity_type=str(raw_response["entity_type"]),
                survey_id=str(raw_response["survey_id"]),
                answers=raw_response["answers"],
            )
        )

    return responses


house_responses = [
    SurveyResponse(
        entity_id="house_1",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Toledo, Ohio, in the Midwest. This is a small urban city with moderate "
                "density and a walkability score of about 61. Local buses provide moderate "
                "coverage, and daily life is moderately car-dependent. Detroit is about "
                "55 miles away. The neighborhood has moderate street noise and moderate "
                "backyard privacy."
            ),
            "cost_and_property": (
                "The estimated purchase price is $139,000, with total monthly housing "
                "costs around $1,250. It is a 1928 detached two-story house with about "
                "1,450 square feet, a 5,200-square-foot lot, three bedrooms, one and a "
                "half bathrooms, a detached one-car garage, a driveway, and a small "
                "fenced backyard with a covered porch."
            ),
            "condition_and_features": (
                "The house is livable but has an older interior. The kitchen and bathroom "
                "need cosmetic updates, and older plumbing and electrical components "
                "should be inspected. It has gas forced-air heat, central air, moderate "
                "energy efficiency, cable internet, an unfinished basement, attic "
                "storage, and a spare bedroom that could serve as an office."
            ),
            "amenities_and_services": (
                "Grocery stores, pharmacies, parks, clinics, and restaurants are generally "
                "within two to four miles. A public library is about three miles away. "
                "Hospitals, community colleges, and trade programs are accessible within "
                "roughly 15 to 30 minutes by car."
            ),
            "climate_and_environment": (
                "The area has four distinct seasons, cold cloudy winters, and warm humid "
                "summers. Average temperatures range from approximately 43°F for the "
                "annual low to 61°F for the annual high. Annual snowfall is about 37 "
                "inches. Relevant hazards include winter storms, freezing temperatures, "
                "flooding, and severe thunderstorms."
            ),
            "community_and_culture": (
                "Toledo is an affordable legacy industrial city with strong neighborhood "
                "identities, local festivals, arts organizations, parks, museums, and "
                "minor-league sports. It is moderately diverse and generally practical "
                "and community-oriented, with established immigrant and newcomer communities."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, manufacturing, logistics, education, and municipal services "
                "are important employment sectors. Nursing, healthcare support, skilled "
                "manufacturing, warehousing, trucking, teaching, and building maintenance "
                "are in demand. Advantages include low cost, a yard, reasonable walkability, "
                "and good basic amenities. Tradeoffs include cold winters, an aging house, "
                "limited transit, and renovation needs."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_2",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Bangor, Maine, in the Northeast. It is a quiet small city with low to "
                "moderate density and a walkability score near 55. Local buses exist but "
                "evening service is limited, so a car is moderately to highly useful. "
                "Portland is approximately 130 miles away. The property is very quiet "
                "and has high privacy because of its wooded lot."
            ),
            "cost_and_property": (
                "The purchase price is approximately $164,000, with monthly housing costs "
                "around $1,450. The property is a 1947 detached Cape-style house with "
                "1,320 square feet, a 9,000-square-foot wooded lot, three bedrooms, one "
                "and a half bathrooms, a two-car detached garage, a deck, and garden space."
            ),
            "condition_and_features": (
                "The house is in good overall condition with recent updates. The kitchen "
                "and one bathroom could be modernized. Maintenance includes snow removal, "
                "exterior painting, and monitoring older basement windows. It uses oil "
                "heat and window air conditioners. Internet is generally good, and the "
                "house has a full basement, attic, garage, and excellent quiet-work potential."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, cafes, clinics, libraries, parks, and river "
                "recreation are available within roughly two to five miles. A regional "
                "hospital is about ten minutes away. Community college and vocational "
                "programs are nearby."
            ),
            "climate_and_environment": (
                "Bangor has cold, snowy winters and mild summers. Average temperatures "
                "range from about 38°F to 55°F, with approximately 75 inches of annual "
                "snowfall. The area is forested and close to rivers and lakes. Major "
                "hazards include heavy snow, ice storms, flooding, and extreme winter cold."
            ),
            "community_and_culture": (
                "The city has a quiet New England character with strong outdoor and local "
                "community traditions. Residents enjoy hiking, fishing, boating, skiing, "
                "cafes, small theaters, music, and seasonal events. Diversity is low to "
                "moderate, and newcomers may experience a slower pace of social integration."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, education, government, retail, construction, and hospitality "
                "are important sectors. Nurses, medical assistants, teachers, electricians, "
                "carpenters, home-health aides, and restaurant workers are in demand. The "
                "house offers quiet, privacy, storage, and recreation, but has high snowfall, "
                "limited large-city employment, car dependence, and an older heating system."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_3",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Erie, Pennsylvania, in the Northeast. This is a small urban city with "
                "moderate density and a walkability score around 64. Local buses provide "
                "moderate coverage, and daily life is moderately car-dependent. Cleveland "
                "is about 100 miles away. The residential area has moderate noise and "
                "moderate privacy."
            ),
            "cost_and_property": (
                "The house costs approximately $128,000, with monthly housing costs near "
                "$1,190. It is a 1915 detached two-story house with about 1,680 square "
                "feet, a 6,000-square-foot lot, four bedrooms, one and a half bathrooms, "
                "a detached two-car garage, a fenced backyard, porch, and patio."
            ),
            "condition_and_features": (
                "The house is usable with a mix of renovated and dated rooms. The bathroom "
                "needs modernization, and the basement should be checked for moisture. "
                "Older roof sections and exterior trim require monitoring. It has gas "
                "forced-air heat, central air, cable or fiber internet, a full basement, "
                "and garage storage, but it is not wheelchair accessible."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, lakefront parks, libraries, hospitals, clinics, "
                "a community college, a university, and trade programs are generally within "
                "five to fifteen minutes by car or bus."
            ),
            "climate_and_environment": (
                "Erie has cool, cloudy, snowy weather influenced by Lake Erie. Average "
                "temperatures range from approximately 40°F to 57°F, and annual snowfall "
                "is around 89 inches. Lakefront parks and recreation are nearby. The main "
                "hazards are lake-effect snow, ice, winter storms, and localized flooding."
            ),
            "community_and_culture": (
                "Erie is an affordable, established, working-class lake city with historic "
                "neighborhoods, local institutions, parks, lakefront activities, festivals, "
                "museums, theaters, and minor-league sports. It is moderately diverse and "
                "generally community-oriented and family-focused."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, manufacturing, logistics, education, and hospitality provide "
                "many jobs, including nursing, healthcare support, machining, welding, "
                "warehousing, teaching, and food service. The house is unusually affordable "
                "and has four bedrooms and lake access, but it has heavy snow, older systems, "
                "some maintenance needs, and fewer high-paying professional jobs."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_4",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Peoria, Illinois, in the Midwest. This is a small urban city with suburban "
                "edges, low to moderate density, and a walkability score around 46. Bus "
                "service is concentrated along major corridors, so daily life is highly "
                "car-dependent. Chicago is approximately 165 miles away. The neighborhood "
                "is quiet and provides good backyard privacy."
            ),
            "cost_and_property": (
                "The purchase price is about $151,000, with monthly housing costs around "
                "$1,320. It is a 1971 detached ranch with approximately 1,550 square feet, "
                "a 10,000-square-foot lot, three bedrooms, two bathrooms, a two-car attached "
                "garage, a large backyard, and a deck."
            ),
            "condition_and_features": (
                "The house is in good condition with dated finishes. Kitchen updates and "
                "flooring replacement are optional. The older HVAC system and deck need "
                "monitoring. It has gas heat, central air, average energy efficiency, "
                "cable or fiber internet, a full basement, a garage, and a mostly "
                "single-level layout."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, parks, river trails, libraries, hospitals, "
                "clinics, community colleges, and trade programs are usually within "
                "10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "The climate has cold winters, warm humid summers, and four seasons. "
                "Average temperatures range from roughly 43°F to 63°F, with about 28 "
                "inches of snow annually. The area has rolling terrain near the Illinois "
                "River. Hazards include severe thunderstorms, tornadoes, flooding, and "
                "winter cold."
            ),
            "community_and_culture": (
                "Peoria is a practical regional center with agricultural, industrial, "
                "and river-city influences. It offers parks, trails, museums, community "
                "sports, festivals, restaurants, local theater, and music. The area is "
                "moderately diverse, quiet, spacious, and family-oriented."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, manufacturing, agriculture, education, and logistics are "
                "important sectors. Nurses, medical technicians, industrial maintenance "
                "workers, equipment operators, truck drivers, teachers, and warehouse "
                "workers are in demand. The house provides space, a yard, garage, and "
                "quiet, but requires a car and has humid summers and limited major-city access."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_5",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Wichita, Kansas, in the Great Plains. It is a spacious mid-sized city "
                "with low to moderate density and a walkability score near 43. Bus service "
                "exists but suburban coverage is limited, making a car highly useful. "
                "Kansas City is about 200 miles away. The neighborhood has low to moderate "
                "noise and good fenced-yard privacy."
            ),
            "cost_and_property": (
                "The house costs approximately $168,000, with monthly housing costs around "
                "$1,410. It is a 1968 detached ranch with 1,640 square feet, an 8,500-square-"
                "foot lot, three bedrooms, two bathrooms, a two-car attached garage, and a "
                "fenced backyard with a covered patio."
            ),
            "condition_and_features": (
                "The property is move-in ready. The kitchen appliances are older, and "
                "flooring or cosmetic updates are optional. The roof and HVAC should be "
                "monitored over time. It has gas heat, central air, average energy "
                "efficiency, widespread fiber or cable internet, a partial basement, "
                "a garage, and good remote-work potential."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, parks, trails, recreation centers, libraries, "
                "hospitals, community colleges, aviation programs, and technical schools "
                "are generally within five to fifteen minutes by car."
            ),
            "climate_and_environment": (
                "Wichita has sunny weather, hot summers, cold winters, moderate to high "
                "summer humidity, and about 15 inches of annual snowfall. The landscape "
                "is flat prairie with open skies. Tornadoes, hail, severe thunderstorms, "
                "summer heat, and strong winter winds are the primary hazards."
            ),
            "community_and_culture": (
                "Wichita is a practical, aviation-oriented city with family activities, "
                "parks, cycling paths, lakes, museums, restaurants, concerts, and local "
                "festivals. It is moderately diverse, generally friendly to newcomers, "
                "and feels spacious, suburban, and easygoing."
            ),
            "jobs_and_tradeoffs": (
                "Aviation, manufacturing, healthcare, logistics, and education are major "
                "employment sectors. Aircraft technicians, machinists, welders, nurses, "
                "warehouse workers, truck drivers, and medical assistants are in demand. "
                "The house offers good internet, a garage, affordability, and strong "
                "skilled-trade employment, but is car-dependent and exposed to severe weather."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_6",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Tulsa, Oklahoma, in the South Central region. This is a mid-sized city "
                "with low to moderate density and a walkability score around 49. Buses "
                "serve central corridors, but most suburban errands require a car. "
                "Oklahoma City is approximately 105 miles away. The property has moderate "
                "noise and good fenced-yard privacy."
            ),
            "cost_and_property": (
                "The purchase price is approximately $179,000, with monthly costs near "
                "$1,490. It is a 1959 detached ranch with 1,500 square feet, a 7,500-square-"
                "foot lot, three bedrooms, two bathrooms, a one-car garage, driveway, "
                "covered patio, and mature trees."
            ),
            "condition_and_features": (
                "The house is in good condition with recent repairs. The kitchen is dated, "
                "and the bathroom fixtures could be replaced. Foundation drainage and the "
                "roof should be inspected. It has gas heat, central air, moderate energy "
                "efficiency, fiber or cable internet, limited storage, and a quiet room "
                "that can serve as an office."
            ),
            "amenities_and_services": (
                "Grocery stores, restaurants, parks, trails, libraries, hospitals, "
                "specialty clinics, community colleges, universities, and technical "
                "programs are generally available within 10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "Tulsa has hot humid summers, mild winters, and about eight inches of "
                "annual snow. Average temperatures range from approximately 50°F to 71°F. "
                "The area has rolling prairie, trees, lakes, and outdoor recreation. "
                "Tornadoes, hail, severe thunderstorms, flooding, and summer heat are "
                "important hazards."
            ),
            "community_and_culture": (
                "Tulsa has a growing regional culture with music, arts, Native American "
                "influences, oil-industry history, restaurants, festivals, river trails, "
                "parks, sports, and nearby lakes. It is moderately diverse, socially active, "
                "generally friendly, and more affordable than many larger cities."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, aerospace, energy, manufacturing, logistics, and education "
                "are important sectors. Nurses, aircraft mechanics, industrial technicians, "
                "electricians, truck drivers, warehouse workers, and medical assistants "
                "are in demand. Advantages include warm weather, cultural activity, jobs, "
                "and reasonable costs. Tradeoffs include heat, severe weather, car "
                "dependence, and drainage concerns."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_7",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Little Rock, Arkansas, in the South. It is a mid-sized city with low to "
                "moderate density and a walkability score near 45. Bus service is limited "
                "outside central areas, so a car is highly useful. Memphis is about 140 "
                "miles away. The neighborhood is quiet with good privacy."
            ),
            "cost_and_property": (
                "The home costs approximately $172,000, with monthly housing costs near "
                "$1,450. It is a 1976 detached ranch with 1,580 square feet, a 9,500-square-"
                "foot lot, three bedrooms, two bathrooms, a two-car garage, a deck, and a "
                "large backyard."
            ),
            "condition_and_features": (
                "The house is move-in ready with modest cosmetic wear. Kitchen and flooring "
                "updates are optional. Routine roof, HVAC, termite, and drainage maintenance "
                "is expected. It has an electric heat pump, central air, moderate-to-good "
                "efficiency, fiber or cable internet, attic and shed storage, and a "
                "mostly accessible single-level layout."
            ),
            "amenities_and_services": (
                "Supermarkets, pharmacies, restaurants, parks, libraries, hospitals, "
                "clinics, community colleges, universities, and trade programs are "
                "generally within 10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "The area has hot humid summers, mild winters, and only about four inches "
                "of annual snow. Average temperatures range from about 51°F to 72°F. "
                "The landscape is hilly, wooded, and near the Arkansas River. Tornadoes, "
                "severe thunderstorms, flash flooding, hurricanes' regional effects, and "
                "summer heat are relevant hazards."
            ),
            "community_and_culture": (
                "Little Rock is a diverse Southern regional capital with government, "
                "healthcare, arts, food, outdoor, and civic traditions. It offers river "
                "trails, parks, museums, restaurants, music, festivals, and community "
                "events. The atmosphere varies by neighborhood but is generally friendly "
                "and newcomer-friendly."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, government, education, retail, logistics, and construction "
                "are major sectors. Nurses, healthcare aides, teachers, truck drivers, "
                "electricians, and construction workers are in demand. The house offers "
                "mild winters, healthcare access, a large yard, and outdoor recreation, "
                "but is car-dependent and exposed to heat, storms, and flooding."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_8",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Birmingham, Alabama, in the Southeast. This is a suburban neighborhood "
                "in a mid-sized metropolitan area, with a walkability score around 34. "
                "Bus service is limited in the suburbs, making a car highly important. "
                "Atlanta is approximately 150 miles away. The home is quiet and private "
                "because of its wooded lot."
            ),
            "cost_and_property": (
                "The estimated price is $178,000, with monthly costs around $1,480. It is "
                "a 1964 detached brick ranch with 1,520 square feet, an 11,000-square-foot "
                "lot, three bedrooms, two bathrooms, a two-car carport, driveway, patio, "
                "and large wooded backyard."
            ),
            "condition_and_features": (
                "The house is in generally good condition but has older finishes. The "
                "kitchen is dated, and crawl-space drainage should be checked. Termite "
                "prevention and roof and drainage maintenance are important. It has gas "
                "heat, central air, below-average energy efficiency, fiber or cable "
                "internet, and a single-level interior with several exterior steps."
            ),
            "amenities_and_services": (
                "Groceries, restaurants, parks, trails, libraries, hospitals, specialty "
                "care, universities, community colleges, and trade schools are generally "
                "within 10 to 20 minutes by car. Birmingham has particularly strong "
                "healthcare access."
            ),
            "climate_and_environment": (
                "Birmingham has very hot, very humid summers, mild winters, and almost "
                "no snow. Average temperatures range from roughly 53°F to 73°F. The "
                "area is green, hilly, and wooded. Tornadoes, severe thunderstorms, "
                "flash flooding, summer heat, and occasional ice storms are hazards."
            ),
            "community_and_culture": (
                "Birmingham is a highly diverse historic Southern city with strong food, "
                "music, civil-rights, healthcare, and arts traditions. It offers hiking, "
                "parks, gardens, museums, festivals, restaurants, and music. The social "
                "environment varies by neighborhood but is generally community-oriented "
                "and welcoming to newcomers."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, biotechnology, education, manufacturing, construction, and "
                "logistics are important sectors. Nurses, medical technicians, healthcare "
                "aides, welders, electricians, warehouse workers, and teachers are in "
                "demand. The home offers diversity, healthcare, warmth, a wooded yard, "
                "and cultural activity, but also high humidity, car dependence, and storm "
                "and flood risk."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_9",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Jackson, Mississippi, in the Southeast. It is a low-density small-to-mid-"
                "sized city with a walkability score near 31. Bus service is limited and "
                "daily life is very car-dependent. New Orleans is about 190 miles away. "
                "The residential street is quiet and offers good privacy."
            ),
            "cost_and_property": (
                "The property costs approximately $132,000, with monthly housing expenses "
                "near $1,190. It is a 1972 detached house with 1,480 square feet, a "
                "12,000-square-foot lot, three bedrooms, two bathrooms, covered parking, "
                "a large yard, mature trees, and a screened porch."
            ),
            "condition_and_features": (
                "The house is livable but has older systems. Cosmetic updates and possible "
                "bathroom renovation are needed. Roof, drainage, termite, and plumbing "
                "issues require attention. It has an electric heat pump, central air, "
                "average-to-below-average efficiency, cable or limited fiber internet, "
                "a shed, and a single-level layout."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, parks, libraries, hospitals, clinics, community "
                "colleges, universities, and workforce-training programs are generally "
                "within 15 to 25 minutes by car."
            ),
            "climate_and_environment": (
                "Jackson has very hot, very humid summers and short mild winters, with "
                "almost no snow. Average temperatures range from about 57°F to 76°F. "
                "The area is flat to gently rolling, wooded, and green. Hazards include "
                "severe thunderstorms, tornadoes, flooding, summer heat, and regional "
                "effects from hurricanes."
            ),
            "community_and_culture": (
                "Jackson has strong Southern traditions involving music, food, churches, "
                "civic organizations, and community events. It is highly diverse and "
                "offers parks, museums, festivals, sports, and local arts. The social "
                "environment is relationship-oriented and varies substantially by area."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, government, education, manufacturing, utilities, and "
                "transportation are important sectors. Nurses, healthcare aides, teachers, "
                "government workers, equipment operators, truck drivers, and electricians "
                "are in demand. The main strengths are very low cost, warm winters, a large "
                "yard, and diversity. Weaknesses include limited transit, heat, storms, "
                "older systems, and a smaller professional job market."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_10",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Fayetteville, North Carolina, in the Southeast. It is a moderately dense "
                "mid-sized city with suburban neighborhoods and a walkability score around "
                "42. Local buses provide moderate coverage, but a car is still important. "
                "Raleigh is about 65 miles away. The area is moderately noisy, including "
                "occasional military-aircraft noise, with moderate privacy."
            ),
            "cost_and_property": (
                "The purchase price is about $185,000, with monthly costs near $1,530. "
                "The house is a 1985 detached ranch with 1,570 square feet, a 9,000-square-"
                "foot lot, three bedrooms, two bathrooms, a two-car garage, a fenced yard, "
                "a patio, and a storage shed."
            ),
            "condition_and_features": (
                "The home is move-in ready with modest cosmetic wear. Flooring and kitchen "
                "counter updates are optional. It needs routine roof, HVAC, and drainage "
                "maintenance. It has an electric heat pump, central air, moderate-to-good "
                "efficiency, fiber or cable internet, attic and garage storage, and a "
                "mostly accessible single-level layout."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, parks, recreation centers, libraries, hospitals, "
                "military healthcare facilities, community colleges, and trade programs are "
                "usually within five to fifteen minutes by car."
            ),
            "climate_and_environment": (
                "The climate is warm and humid with mild winters, hot summers, and about "
                "two inches of annual snow. Average temperatures range from approximately "
                "53°F to 73°F. Pine forests and gently rolling terrain surround the area. "
                "Hurricanes, heavy rain, flooding, severe thunderstorms, and heat are risks."
            ),
            "community_and_culture": (
                "Fayetteville is a diverse, military-connected community accustomed to "
                "frequent newcomers. It offers parks, golf, sports, lakes, restaurants, "
                "concerts, community events, and international influences. It feels "
                "suburban, practical, mobile, and family-oriented."
            ),
            "jobs_and_tradeoffs": (
                "Military and defense, healthcare, education, logistics, construction, "
                "retail, and public services are important sectors. Healthcare aides, "
                "medical technicians, truck drivers, security workers, electricians, "
                "teachers, and warehouse workers are in demand. Strengths include warmth, "
                "diversity, family services, and degree-free jobs. Tradeoffs include "
                "humidity, storm risk, car dependence, and aircraft noise."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_11",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Pueblo, Colorado, in the Mountain West. It is a small city with low to "
                "moderate density and a walkability score around 48. Local buses exist "
                "but regional service is limited, so a car is moderately to highly useful. "
                "Colorado Springs is approximately 45 miles away. The area is generally "
                "quiet with moderate privacy and mountain views."
            ),
            "cost_and_property": (
                "The estimated price is $205,000, with monthly costs around $1,680. This "
                "is a 1958 detached ranch with 1,360 square feet, a 7,000-square-foot lot, "
                "three bedrooms, one bathroom, a detached one-car garage, xeriscaped yard, "
                "and patio."
            ),
            "condition_and_features": (
                "The furnace and roof were recently updated, but the kitchen and bathroom "
                "are dated. The dry climate requires exterior maintenance and occasional "
                "plumbing work. The house has gas heat, an evaporative cooler, moderate "
                "energy efficiency, cable or limited fiber internet, a shed, and a "
                "mostly single-level layout."
            ),
            "amenities_and_services": (
                "Supermarkets, restaurants, parks, river trails, libraries, hospitals, "
                "clinics, community colleges, and technical programs are generally within "
                "10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "Pueblo has a dry high-plains climate with sunny days, cold nights, warm "
                "summers, and roughly 32 inches of snow per year. Average temperatures "
                "range from about 39°F to 65°F. The area has grasslands, foothills, and "
                "mountain views. Drought, wildfire smoke, high winds, hail, and occasional "
                "heavy snow are the main hazards."
            ),
            "community_and_culture": (
                "Pueblo is a relaxed, working-class Colorado city with strong Hispanic "
                "and Western influences. Residents enjoy hiking, fishing, cycling, parks, "
                "museums, festivals, local food, and access to mountain destinations. "
                "The city is moderately diverse, practical, spacious, and less polished "
                "than larger Colorado cities."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, manufacturing, construction, energy, education, and food "
                "processing are important sectors. Nurses, welders, machinists, electricians, "
                "healthcare aides, truck drivers, and teachers are in demand. Strengths "
                "include dry weather, outdoor access, lower costs than major Colorado cities, "
                "and skilled-trade opportunities. Tradeoffs include limited transit, drought, "
                "wildfire smoke, and a smaller job market."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_12",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Albuquerque, New Mexico, in the Southwest. It is a spread-out mid-sized "
                "city with a walkability score around 51. Bus and rapid-bus routes serve "
                "some corridors, but a car is moderately important. Santa Fe is about 65 "
                "miles away. The property has low to moderate noise and good courtyard privacy."
            ),
            "cost_and_property": (
                "The house costs approximately $218,000, with monthly housing costs near "
                "$1,790. It is a 1975 detached adobe-style ranch with 1,450 square feet, "
                "a 7,200-square-foot lot, three bedrooms, two bathrooms, a one-car garage, "
                "a xeriscaped courtyard, and a covered patio."
            ),
            "condition_and_features": (
                "The house is in good condition with Southwestern architectural features. "
                "The kitchen needs updates and the exterior stucco needs some repair. Roof "
                "coating, evaporative-cooler, and stucco maintenance are expected. It has "
                "gas heat, an evaporative cooler, moderate efficiency, fiber or cable "
                "internet, storage space, and a mostly flat single-level interior."
            ),
            "amenities_and_services": (
                "Supermarkets, local markets, restaurants, parks, trails, libraries, "
                "hospitals, specialty clinics, universities, community colleges, and "
                "technical schools are generally within 10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "Albuquerque has a sunny, dry high-desert climate with large daily "
                "temperature swings. Average temperatures range from about 47°F to 70°F, "
                "with roughly ten inches of annual snow. Mountains, desert parks, and "
                "outdoor recreation are nearby. Drought, wildfire smoke, flash flooding, "
                "high winds, and summer heat are relevant hazards."
            ),
            "community_and_culture": (
                "The city has a distinctive, highly diverse Southwestern culture shaped "
                "by Hispanic, Native, artistic, culinary, and scientific traditions. "
                "It offers art markets, museums, music, local cuisine, cultural festivals, "
                "hiking, cycling, climbing, and nearby skiing. The atmosphere is creative, "
                "independent, spread out, and generally welcoming to newcomers."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, government, research, technology, construction, and education "
                "are important sectors. Nurses, laboratory technicians, IT support workers, "
                "electricians, construction workers, teachers, and government analysts are "
                "in demand. Strengths include dry weather, cultural identity, healthcare, "
                "education, and outdoor access. Tradeoffs include water scarcity, drought, "
                "wildfire smoke, flash flooding, and spread-out development."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_13",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Spokane, Washington, in the Pacific Northwest. It is a mid-sized city "
                "with low to moderate density, a walkability score near 52, and a bus "
                "network with moderate coverage. Daily life is moderately to highly "
                "car-dependent. Seattle is approximately 280 miles away. The neighborhood "
                "is quiet to moderately noisy and provides good backyard privacy."
            ),
            "cost_and_property": (
                "The purchase price is approximately $239,000, with monthly costs near "
                "$1,940. It is a 1940 detached craftsman house with 1,420 square feet, "
                "a 6,500-square-foot lot, three bedrooms, one bathroom, a detached one-car "
                "garage, a deck, mature trees, and a fenced yard."
            ),
            "condition_and_features": (
                "The house combines historic details with modern updates. The bathroom "
                "needs expansion and the kitchen needs better storage. Older plumbing, "
                "exterior paint, and the roof require monitoring. It has gas heat, central "
                "air, moderate efficiency, fiber or cable internet, basement and attic "
                "storage, and several entry steps."
            ),
            "amenities_and_services": (
                "Supermarkets, local stores, restaurants, cafes, breweries, parks, river "
                "trails, libraries, hospitals, clinics, community colleges, universities, "
                "and trade programs are generally within 10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "Spokane has a dry inland Northwest climate with snowy winters and warm "
                "summers. Average temperatures range from approximately 40°F to 61°F, "
                "with about 45 inches of annual snow. The area has forests, hills, rivers, "
                "and nearby lakes. Wildfire smoke, snow, freezing temperatures, drought, "
                "and occasional flooding are relevant hazards."
            ),
            "community_and_culture": (
                "Spokane is an outdoor-oriented regional city with universities, arts, "
                "breweries, older neighborhoods, restaurants, music, theaters, and local "
                "events. It offers hiking, skiing, cycling, lakes, and river trails. "
                "The population is moderately diverse, and the social environment is "
                "relaxed, independent, and somewhat reserved."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, education, aerospace, manufacturing, construction, and "
                "logistics are important sectors. Nurses, medical assistants, teachers, "
                "machinists, electricians, warehouse workers, and construction laborers "
                "are in demand. Strengths include outdoor recreation, internet, healthcare, "
                "and dry summers. Tradeoffs include winter snow, wildfire smoke, an older "
                "house, and limited access to large coastal cities."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_14",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Fresno, California, in Central California. It is a moderately dense "
                "mid-sized city with a walkability score around 44. Bus service is "
                "available but daily life is highly car-dependent. The property is about "
                "110 miles from Bakersfield and within driving distance of mountain areas. "
                "Traffic noise is moderate and backyard privacy is moderate."
            ),
            "cost_and_property": (
                "The estimated price is $285,000, with monthly housing expenses near "
                "$2,260. It is a 1978 detached ranch with 1,540 square feet, a 7,200-square-"
                "foot lot, three bedrooms, two bathrooms, a two-car garage, a fenced yard, "
                "covered patio, and citrus trees."
            ),
            "condition_and_features": (
                "The house is move-in ready with moderate-quality finishes. Kitchen updates "
                "and drought-tolerant landscaping are optional. Roof, HVAC, irrigation, "
                "and exterior paint require routine maintenance. It has gas heat, central "
                "air, moderate efficiency, widespread fiber or cable internet, garage and "
                "attic storage, and an accessible single-level layout."
            ),
            "amenities_and_services": (
                "Supermarkets, shopping centers, restaurants, parks, libraries, hospitals, "
                "clinics, community colleges, universities, trade schools, and agricultural "
                "services are generally within 10 to 20 minutes by car."
            ),
            "climate_and_environment": (
                "Fresno has hot, dry summers and mild wetter winters, with no meaningful "
                "snow. Average temperatures range from approximately 52°F to 75°F. The "
                "area is agricultural and provides access to foothills and mountains. "
                "Extreme heat, drought, wildfire smoke, seasonal air-quality problems, "
                "and occasional flooding are concerns."
            ),
            "community_and_culture": (
                "Fresno is a highly diverse Central Valley city with strong Hispanic, "
                "Asian, immigrant, agricultural, and family communities. It offers varied "
                "restaurants, cultural festivals, shopping, parks, sports, and access to "
                "outdoor areas. The general atmosphere is warm, practical, suburban, and "
                "strongly car-oriented."
            ),
            "jobs_and_tradeoffs": (
                "Agriculture, food processing, healthcare, logistics, education, and "
                "construction are major sectors. Farm and equipment workers, food-processing "
                "workers, nurses, warehouse workers, truck drivers, mechanics, and teachers "
                "are in demand. Strengths include warmth, diversity, a single-level house, "
                "and strong degree-free employment. Tradeoffs include heat, drought, air "
                "quality, high car dependence, and a higher price."
            ),
        },
    ),

    SurveyResponse(
        entity_id="house_15",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Rochester, New York, in the Northeast. It is a small urban city with "
                "moderate density, selected walkable neighborhoods, and a walkability "
                "score around 67. Bus service is moderately useful, and daily life is "
                "moderately car-dependent. Buffalo is approximately 75 miles away. The "
                "house has moderate urban noise and moderate backyard privacy."
            ),
            "cost_and_property": (
                "The purchase price is about $156,000, with monthly costs near $1,380. "
                "It is a 1935 detached two-story colonial-style house with 1,710 square "
                "feet, a 6,200-square-foot lot, four bedrooms, one and a half bathrooms, "
                "a detached one-car garage, a fenced yard, porch, and garden area."
            ),
            "condition_and_features": (
                "The home is livable with modern updates and historic details. The kitchen "
                "and upstairs bathroom would benefit from renovation. The basement, roof, "
                "windows, and exterior trim require monitoring. It has gas heat, central "
                "air, moderate efficiency, cable or fiber internet, basement and attic "
                "storage, several potential office spaces, and limited accessibility "
                "because bedrooms and the full bathroom are upstairs."
            ),
            "amenities_and_services": (
                "Supermarkets, food stores, restaurants, cafes, parks, lake access, "
                "libraries, hospitals, clinics, universities, community colleges, and "
                "trade programs are generally within five to fifteen minutes by car, "
                "bus, bicycle, or walking depending on the neighborhood."
            ),
            "climate_and_environment": (
                "Rochester has a cold four-season climate with snowy winters and pleasant "
                "summers. Average temperatures range from roughly 42°F to 59°F, with about "
                "100 inches of annual snowfall. The region has parks, trees, waterways, "
                "and lake access. Heavy snow, ice storms, freezing temperatures, flooding, "
                "and severe thunderstorms are relevant hazards."
            ),
            "community_and_culture": (
                "Rochester is a historic, highly diverse upstate city with universities, "
                "arts, immigrant communities, neighborhood festivals, museums, theaters, "
                "music, restaurants, parks, and lake recreation. Selected neighborhoods "
                "are walkable and culturally active. The city is generally community-"
                "oriented and welcoming to newcomers."
            ),
            "jobs_and_tradeoffs": (
                "Healthcare, higher education, advanced manufacturing, technology, logistics, "
                "and education are important sectors. Nurses, medical technicians, teachers, "
                "machinists, IT support workers, warehouse workers, and home-health aides "
                "are in demand. Strengths include four bedrooms, walkability, healthcare, "
                "education, diversity, and cost. Tradeoffs include heavy snow, older systems, "
                "limited accessibility, and renovation needs."
            ),
        },
    ),
]