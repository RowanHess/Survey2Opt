"""Heterogeneous Boston house-survey examples for matching experiments.

The address, sale, assessment, building, size, room, HVAC, condition, and
parking facts are drawn from the City of Boston FY26 property-assessment and
latest-sales tables. Boston does not publish free-form resident surveys for
these properties. The survey-like observations below are inferred from the
records and general neighborhood context. They intentionally vary in voice,
length, organization, specificity, and uncertainty.

Sources retrieved 2026-08-19:
https://gisportal.boston.gov/arcgis/rest/services/Assessing/properties_boston_gov/FeatureServer/0
https://gisportal.boston.gov/arcgis/rest/services/Assessing/properties_boston_gov/FeatureServer/11
"""

from surveyopt.models import (
    SurveyDefinition,
    SurveyQuestion,
    SurveyResponse,
)


house_survey = SurveyDefinition(
    id="house_survey",
    respondent_type="house",
    questions=[
        SurveyQuestion(
            id="location_and_transportation",
            text=(
                "In any natural format, describe where the property is and what daily "
                "transportation, walkability, noise, and privacy are likely to be like."
            ),
        ),
        SurveyQuestion(
            id="cost_and_property",
            text=(
                "Describe the recorded price and physical property. Include whichever "
                "cost, size, room, parking, lot, or outdoor details are known."
            ),
        ),
        SurveyQuestion(
            id="condition_and_features",
            text=(
                "What is known or reasonably inferred about condition, renovation, "
                "maintenance, HVAC, efficiency, internet, storage, accessibility, and work space?"
            ),
        ),
        SurveyQuestion(
            id="amenities_and_services",
            text=(
                "Describe useful nearby amenities and services. Approximate or incomplete "
                "answers are acceptable when exact travel times are unavailable."
            ),
        ),
        SurveyQuestion(
            id="climate_and_environment",
            text=(
                "Describe relevant weather, scenery, recreation, and environmental hazards "
                "for this property or neighborhood."
            ),
        ),
        SurveyQuestion(
            id="community_and_culture",
            text=(
                "How would you characterize the surrounding community, culture, social life, "
                "and general atmosphere?"
            ),
        ),
        SurveyQuestion(
            id="jobs_and_tradeoffs",
            text=(
                "Discuss access to work, including degree-free opportunities, and give the "
                "property's important advantages, disadvantages, and unresolved questions."
            ),
        ),
    ],
)


house_responses = [
    SurveyResponse(
        entity_id="boston_house_01",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "20 Radcliffe Road, Unit 211, Allston. Dense and busy rather than private. "
                "Green Line and buses make a car optional, while the included parking space also "
                "supports driving. The surrounding student and nightlife activity creates a lively, "
                "sometimes noisy setting."
            ),
            "cost_and_property": (
                "This 1945 low-rise condo is an exceptionally compact home with one bedroom and one "
                "bathroom in only 418 square feet. It has no private yard, but it does include one parking "
                "space. The property sold for $315,000 in October 2025, is assessed at $325,900, and carries "
                "$4,041 in gross annual property tax."
            ),
            "condition_and_features": (
                "The 1945 condo is in average condition and retains steam or hot-water heat without "
                "central air conditioning. Its compact layout provides little storage or separation "
                "between living and working space, so a dining table or bedroom corner would likely "
                "serve as the home office."
            ),
            "amenities_and_services": (
                "Groceries, takeout, restaurants, music, pharmacies, parks, the Honan-Allston "
                "library, and access toward BU and Harvard. Major hospitals are a transit trip."
            ),
            "climate_and_environment": (
                "Allston has cold, snowy winters and humid summers, with dense blocks that retain heat "
                "and provide little private greenery. Heavy rain and the nearby Charles River add some "
                "flooding exposure, while neighborhood parks provide the main outdoor relief."
            ),
            "community_and_culture": (
                "Young, diverse, informal, lots of students and newcomers. Strong restaurant and "
                "live-music culture. Easy to meet people; not a calm suburban setting."
            ),
            "jobs_and_tradeoffs": (
                "Good transit to education, healthcare, service, restaurant, retail, and office jobs. "
                "Win: low entry price plus parking. Loss: 418 square feet, no office or central AC, "
                "with very limited room for more than one resident."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_02",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Beacon Hill, 32 Hancock Street, Unit 2B. Extremely central; walk, subway, or bus "
                "for most things. The property has no parking, and the narrow streets, visitors, and "
                "constant city sounds create less privacy than a quiet residential neighborhood."
            ),
            "cost_and_property": (
                "Built in 1970, this 1,100-square-foot mid-rise condo provides two bedrooms and two full "
                "bathrooms, emphasizing comfortable interior space rather than a private yard. It sold for "
                "$1.53 million in October 2025, has a $1,105,200 assessment, and carries $13,704 in gross "
                "annual property tax."
            ),
            "condition_and_features": (
                "The 1970 condo is in average condition, with hot-water or steam heat and no central "
                "air. Its two full bathrooms make the space comfortable for a couple or roommates, "
                "and the second bedroom can become a dedicated office when it is not needed for sleeping."
            ),
            "amenities_and_services": (
                "Boston Common, Esplanade, food, pharmacies, MGH, downtown libraries, and cultural "
                "venues. Many errands should be walkable."
            ),
            "climate_and_environment": (
                "Four-season coastal weather. Heat in dense masonry blocks and winter ice on old "
                "sidewalks may matter more day to day than yard maintenance."
            ),
            "community_and_culture": (
                "Historic, polished, civic, touristy, expensive. More formal than Allston. Beautiful "
                "streets and immediate culture, but little seclusion during busy hours."
            ),
            "jobs_and_tradeoffs": (
                "Excellent access to hospitals, government, finance, hospitality, universities, and "
                "downtown trades. The premium location and two bathrooms are balanced by the high cost, "
                "absence of parking and central cooling, limited outdoor space, and less privacy than a detached home."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_03",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The penthouse at 100 Lovejoy Wharf sits beside North Station, making subway, "
                "commuter rail, bus, and walking practical enough for a car-free household. The "
                "same central location brings arena crowds, train activity, and event-day noise, "
                "and the property does not include a parking space."
            ),
            "cost_and_property": (
                "The 2017 high-rise penthouse offers 1,644 square feet with three bedrooms and two and a "
                "half bathrooms, making it one of the largest and newest condos in the group. Its October "
                "2025 sale price was $2,424,000, with a $2,026,600 assessment and $25,130 in gross annual tax."
            ),
            "condition_and_features": (
                "Built and finished in 2017, the unit has forced-air heat, central air conditioning, "
                "and an average recorded condition. Three bedrooms create room for a closed office "
                "without sacrificing all guest space, while high-rise elevator access is more convenient "
                "for limited mobility than the older walk-up properties."
            ),
            "amenities_and_services": (
                "North Station, TD Garden, North End, waterfront paths, supermarkets, restaurants, "
                "MGH, commuter rail, and several subway lines. Exceptionally strong no-car access."
            ),
            "climate_and_environment": (
                "The harbor-edge position is exposed to strong winds, coastal storms, and flooding, "
                "although high-rise living removes most yard and snow-clearing work. Central cooling "
                "makes humid summers more comfortable, while waterfront paths provide convenient recreation."
            ),
            "community_and_culture": (
                "The area blends new residential towers with historic Boston, daily commuters, North End "
                "culture, and large sports crowds. It feels energetic and convenient rather than intimate "
                "or secluded."
            ),
            "jobs_and_tradeoffs": (
                "Strong for downtown, hospital, tech, finance, or remote workers. Exceptional connectivity, "
                "space, and newer systems for the highest price here, probable large fees, event noise, "
                "and coastal exposure."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_04",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "357 Faneuil Street #12 is in quieter, outer Brighton. Buses are more immediate than "
                "rapid transit. One parking spot supports a mixed car/transit routine."
            ),
            "cost_and_property": (
                "This 1973 low-rise condo fits two bedrooms and one bathroom into 755 square feet and "
                "includes one parking space. It sold for $440,000 in October 2025, is assessed at $335,000, "
                "and has $4,154 in gross annual property tax."
            ),
            "condition_and_features": (
                "The condo is in average condition and was last remodeled in 1986, leaving it more "
                "dated than recently renovated homes. It has forced-air heat but no central cooling. "
                "A single resident or couple could use the second bedroom as a quiet office."
            ),
            "amenities_and_services": (
                "Supermarkets, pharmacies, restaurants, parks, a library, St. Elizabeth's, and nearby "
                "colleges. Some errands may be walkable; others need a bus or short drive."
            ),
            "climate_and_environment": (
                "Boston winter and humid summer. Less harbor exposure than East Boston, but localized "
                "drainage, icy streets, and summer heat are plausible."
            ),
            "community_and_culture": (
                "Families, students, professionals, immigrants, and long-term residents. Quieter than "
                "Allston nightlife but not socially isolated."
            ),
            "jobs_and_tradeoffs": (
                "Useful for education, healthcare, retail, restaurant, and service work. Moderate price "
                "and parking help; small size, one bath, no AC, dated remodel, fees, and slower transit do not."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_05",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "My read of 18 Park Street, Charlestown: urban row-house block, walkable daily needs, "
                "buses nearby and Orange Line in the neighborhood. I would not count on a car: zero parking."
            ),
            "cost_and_property": (
                "The home is a 1,293-square-foot end-row condo dating to 1900, with two bedrooms and one "
                "and a half bathrooms but little private outdoor space. It sold for $850,000 in October "
                "2025, is assessed at $715,400, and carries $8,871 in gross annual tax."
            ),
            "condition_and_features": (
                "The 1900 row building is in average condition and was remodeled in 1988, leaving "
                "older systems and finishes than a modern condo. Steam or hot-water heat serves the "
                "home, but there is no central cooling. The generous living area can hold a desk, "
                "though neither bedroom is naturally expendable as an office."
            ),
            "amenities_and_services": (
                "Library, neighborhood food and shops, parks, Freedom Trail, waterfront paths, and short "
                "trips to downtown or MGH give the property strong everyday and cultural access. Groceries "
                "and schools are available throughout the surrounding neighborhood."
            ),
            "climate_and_environment": (
                "The older building may be draftier during snowy winters and warmer during humid summers. "
                "Charlestown's coastal setting adds storm and flooding exposure, while nearby waterfront "
                "paths provide convenient outdoor recreation."
            ),
            "community_and_culture": (
                "Strong local identity, Irish-American history, tourism, waterfront recreation, and a mix "
                "of established and newer professional households."
            ),
            "jobs_and_tradeoffs": (
                "Close to healthcare, government, trades, construction, hospitality, and office work. "
                "The home is spacious, central, and rich in historic character, but it is expensive for two "
                "bedrooms and combines shared walls, interior stairs, older systems, no parking, and no cooling."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_06",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "103 Russell Street #2 is in an urban Charlestown neighborhood with bus and Orange Line "
                "connections that keep downtown trips short. Its included parking space adds flexibility, "
                "while the free-standing building provides more privacy than a typical row house."
            ),
            "cost_and_property": (
                "Built in 2006, this free-standing condo provides 1,252 square feet, three bedrooms, two "
                "bathrooms, and one parking space. Its 2025 sale price was $1,125,000, while its assessment "
                "is $957,400 and its gross annual property tax is $11,872."
            ),
            "condition_and_features": (
                "The 2006 condo is in good condition, with forced-air heat and central air conditioning. "
                "Its three-bedroom layout supports two sleeping rooms and a separate office, while the "
                "free-standing building offers more separation than a typical row-house condo."
            ),
            "amenities_and_services": (
                "Neighborhood food, schools, a library, parks, historic sites, and waterfront recreation "
                "cover daily and leisure needs, while central Boston hospitals and services are a short trip away."
            ),
            "climate_and_environment": (
                "Snow and ice shape winter travel, while central air provides relief during humid summers. "
                "Charlestown's coastal location brings wind and flooding exposure along with easy access "
                "to waterfront walking and recreation."
            ),
            "community_and_culture": (
                "Charlestown has a strong neighborhood identity shaped by historic streets, waterfront "
                "activity, long-term residents, and newer households, with downtown culture close at hand."
            ),
            "jobs_and_tradeoffs": (
                "The three bedrooms, two baths, parking, central air, and good condition support a "
                "family or remote workers with easy access to central employment. The seven-figure "
                "price buys little private outdoor space and retains city noise and coastal exposure."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_07",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Chestnut Hill edge, 36 Bryon Road. Quiet complex, two parking spaces. Transit exists "
                "in the wider area, but expect to use a car more often here."
            ),
            "cost_and_property": (
                "This modest 1955 condo offers 780 square feet with two bedrooms, one bathroom, and two "
                "parking spaces. It sold for $390,000 in September 2025, is assessed at $364,100, and "
                "has $4,515 in gross annual property tax."
            ),
            "condition_and_features": (
                "The 1955 condo is in average condition and uses steam or hot-water heat without central "
                "air. Its two-bedroom layout is modest but workable for a single resident who wants a "
                "separate office, and the low-rise complex offers a simple residential setting."
            ),
            "amenities_and_services": (
                "Shopping, groceries, parks, medical offices, Boston College, Green Line in larger area. "
                "The setting is less immediately walkable than central Boston, so some errands are better "
                "reached by car or transit."
            ),
            "climate_and_environment": (
                "The greener inland setting has less coastal exposure, but snowy winter driving, tree and "
                "storm cleanup, and humid summer heat without air conditioning shape daily comfort."
            ),
            "community_and_culture": (
                "The surrounding area feels suburban, green, and quiet, with a mixture of students, "
                "families, and professionals. It favors calm residential life over nightlife."
            ),
            "jobs_and_tradeoffs": (
                "Affordable relative to central Boston and two parking spaces. Useful for western education, "
                "healthcare, retail, and service work. The small interior, one bathroom, car-oriented setting, "
                "and lack of air conditioning are its main constraints."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_08",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "39-41 Bishop Joe L. Smith Way in Dorchester 02121. A bus-first location: urban, "
                "residential, connected, but less rail-oriented than downtown. Without on-site parking, "
                "it best suits a household comfortable using buses and occasional ride services."
            ),
            "cost_and_property": (
                "The 2017 low-rise condo contains two bedrooms and one bathroom within 850 square feet. "
                "It sold for $399,000 in October 2025, making it a relatively affordable newer home, and "
                "it is assessed at $352,400 with $4,370 in gross annual property tax."
            ),
            "condition_and_features": (
                "Built in 2017, the condo is in average condition and has forced-air heat without central "
                "air conditioning. Its newer construction carries less age-related maintenance than the "
                "century-old homes, and the second bedroom can serve as a compact office."
            ),
            "amenities_and_services": (
                "Food stores, pharmacies, schools, libraries, health centers, and parks. Franklin Park "
                "and Grove Hall provide larger-area shopping, services, and recreation, generally reached "
                "by a short bus trip or drive."
            ),
            "climate_and_environment": (
                "Not the immediate harbor edge. Urban heat and drainage after intense rain are more "
                "plausible concerns, alongside snow, ice, and humidity."
            ),
            "community_and_culture": (
                "Dorchester is large and varied: long-time Black residents, immigrant communities, "
                "families, churches, local businesses, and major block-by-block differences."
            ),
            "jobs_and_tradeoffs": (
                "Bus access to healthcare, education, retail, food service, construction, and facilities "
                "jobs. The newer building and moderate price are attractive, while one bathroom, no parking "
                "or central cooling, and slower trips to downtown limit its appeal."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_09",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "80 Fuller Street, Unit 1, Dorchester 02124. Residential triple-decker area. "
                "Buses are close and Red Line, Mattapan Line, or commuter rail may be reachable "
                "depending on the route. One parking spot. Moderate city noise, shared-building privacy."
            ),
            "cost_and_property": (
                "This 1905 triple-decker condo was remodeled in 2019 and now offers three bedrooms, two "
                "bathrooms, and one parking space within 977 square feet. It sold for $620,000, is assessed "
                "at $568,700, and carries $7,052 in gross annual property tax."
            ),
            "condition_and_features": (
                "Rated good. Forced-air heating and central cooling. The third bedroom gives an office "
                "option, although rooms may be compact. First-floor unit does not automatically mean "
                "step-free access because triple-decker porch steps are common. The 2019 renovation makes "
                "this one of the more move-in-ready older properties."
            ),
            "amenities_and_services": (
                "Neighborhood groceries, Caribbean food, schools, libraries, clinics, playgrounds, "
                "Franklin Park and the Neponset area. Downtown institutions require transit or driving."
            ),
            "climate_and_environment": (
                "The inland setting is more exposed to urban heat and localized stormwater than direct "
                "harbor surge. Central air improves summer comfort, while the older triple-decker form "
                "still brings typical winter heating and snow concerns."
            ),
            "community_and_culture": (
                "Culturally diverse and family-oriented, with Caribbean, Black, immigrant, and long-"
                "established communities. Strong local identity rather than tourist culture."
            ),
            "jobs_and_tradeoffs": (
                "Good layout for family plus office; parking, AC, two baths, and assessed condition help. "
                "Healthcare support, education, transit, trades, and services are accessible. Shared "
                "building maintenance, compact rooms, and a less direct rail connection are the tradeoffs."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_10",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "258 Lexington Street, East Boston. Dense block, buses and Blue Line in the neighborhood. "
                "No parking; airport and traffic noise possible. Semi-detached with a very small lot, "
                "so do not expect suburban privacy."
            ),
            "cost_and_property": (
                "The 1910 three-family building places 3,121 square feet of living area on a very compact "
                "1,250-square-foot parcel. Its six bedrooms and three full bathrooms are divided across the "
                "three households. It sold for $1,015,000 in October 2025, is assessed at $869,400, and has "
                "$10,781 in gross annual property tax."
            ),
            "condition_and_features": (
                "City condition code: average. Heat code: space heat. AC: none. Remodel year: none. "
                "The three units rely on older space-heating systems and lack central air conditioning. "
                "Its 1910 structure carries a heavier maintenance burden across multiple kitchens, bathrooms, "
                "utility systems, shared exits, and a moisture-prone basement."
            ),
            "amenities_and_services": (
                "East Boston food markets, Latin American restaurants, schools, clinics, library, harbor "
                "parks, airport, and Blue Line access. Downtown is close in distance even when traffic is not."
            ),
            "climate_and_environment": (
                "East Boston's coastal position brings storm-surge, sea-level, and basement-flooding risk. "
                "The airport also contributes noise and air-quality pressure, while the older three-family "
                "building requires substantial winter heating."
            ),
            "community_and_culture": (
                "Vibrant immigrant neighborhood, especially Latino communities; long-term families, local "
                "businesses, waterfront parks, new development, and visible housing pressure."
            ),
            "jobs_and_tradeoffs": (
                "Potential extended-family housing or rental income, and good access to airport, hospitality, "
                "logistics, construction, transit, healthcare, and downtown jobs. The million-dollar price, "
                "landlord responsibilities, old systems, lack of parking and cooling, airport noise, and flood "
                "exposure create a demanding ownership profile."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_11",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "Waterfront East Boston, 45 Lewis Street #409. Walkable to local services and Blue Line "
                "connections. With no included parking, it is best suited to a transit household. The "
                "upper-floor position provides more privacy than a street-level unit, although Logan Airport "
                "and waterfront activity keep the setting lively."
            ),
            "cost_and_property": (
                "This modern 2020 mid-rise condo offers 1,219 square feet with two bedrooms and two "
                "bathrooms. Its $1.6 million sale price reflects the newer waterfront setting, while the "
                "property is assessed at $1,206,300 and carries $14,958 in gross annual tax."
            ),
            "condition_and_features": (
                "The 2020 condo is in average condition and combines forced-air heat with central air "
                "conditioning. Its modern mid-rise form is more accessible than the older walk-ups, and "
                "the second bedroom can function as a dedicated office for a single resident or couple."
            ),
            "amenities_and_services": (
                "Harbor walks, parks, food, pharmacies, library, Blue Line, downtown, and Logan. Strong "
                "regional access without driving; healthcare and universities are one or more transfers away."
            ),
            "climate_and_environment": (
                "The waterfront views and recreation come with direct exposure to coastal flooding, storm "
                "surge, and strong winds. The modern building provides year-round climate control, but major "
                "coastal storms can still disrupt utilities and access."
            ),
            "community_and_culture": (
                "A blend of established East Boston immigrant culture and newer waterfront development. "
                "Diverse, active, food-rich, and changing quickly."
            ),
            "jobs_and_tradeoffs": (
                "Excellent for airport, downtown, hospitality, logistics, finance, government, or remote work. "
                "Newer HVAC and two baths are positives. The high price, no included parking, airport noise, "
                "and waterfront resilience are the difficult side."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_12",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The condo at 175 Clare Avenue sits in quieter, outer Hyde Park, where buses and commuter "
                "rail provide city connections but a car remains useful for everyday errands. One parking "
                "space supports that suburban routine."
            ),
            "cost_and_property": (
                "Sold for $265,000, this 1960 condo is the least expensive property in the set. It offers "
                "810 square feet with two bedrooms and one bathroom, carries a $187,900 assessment, and "
                "has $2,330 in gross annual property tax."
            ),
            "condition_and_features": (
                "The condo is in average condition and uses electric heat with central air conditioning. "
                "Although its 810-square-foot interior is compact, the second bedroom gives a single resident "
                "a separate office and the central cooling improves summer comfort."
            ),
            "amenities_and_services": (
                "Local groceries, restaurants, schools, a library, parks, and the Neponset corridor cover "
                "everyday needs. Downtown hospitals and colleges require a longer commuter-rail, bus, or car trip."
            ),
            "climate_and_environment": (
                "The greener inland setting has less direct coastal exposure but brings winter driving, tree "
                "maintenance, and localized river or stormwater flooding. Electric heat can make cold winters costly."
            ),
            "community_and_culture": (
                "Hyde Park combines Boston's cultural diversity with a quieter, family-oriented, suburban "
                "atmosphere centered on local parks, schools, businesses, and civic life."
            ),
            "jobs_and_tradeoffs": (
                "The low price, parking, two bedrooms, and central air make this practical for workers in retail, "
                "care services, schools, trades, facilities, or Readville-area industry. The longer commute, "
                "single bathroom, older construction, and electric heating costs are its main compromises."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_13",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The detached ranch at 60 Stanbro Street sits in lower-density Hyde Park, where two parking "
                "spaces and a quiet residential setting suit a family seeking privacy. Buses and commuter rail "
                "connect the district, although a car still makes everyday errands easier."
            ),
            "cost_and_property": (
                "The detached 1958 ranch offers three bedrooms and one bathroom within a compact 950-square-"
                "foot interior, surrounded by a much larger 6,666-square-foot lot. It sold for $450,000 in "
                "October 2025, is assessed at $524,900, and carries $6,509 in gross annual property tax."
            ),
            "condition_and_features": (
                "The ranch is in average condition, with hot-water or steam heat and no central air. Its "
                "single-story form reduces interior stair use, but three bedrooms within only 950 square feet "
                "create compact rooms, and a closed office would consume one sleeping room."
            ),
            "amenities_and_services": (
                "Hyde Park center, groceries, schools, parks, library and commuter rail are in the larger area. "
                "The lower-density setting puts some daily errands beyond a short walk, making transit or "
                "driving more useful than in central neighborhoods."
            ),
            "climate_and_environment": (
                "A yard for gardening and play, plus yard work, leaves, snow, and drainage. Inland river and "
                "stormwater exposure can affect the area, and humid summers may be uncomfortable without AC."
            ),
            "community_and_culture": (
                "City diversity with a suburban, family-focused rhythm. Less nightlife, more local parks, "
                "schools, community groups, and neighborhood-center activity."
            ),
            "jobs_and_tradeoffs": (
                "Detached house, lot, parking and moderate price are rare Boston strengths. Suitable for workers "
                "in schools, healthcare support, trades, transit, warehouses, or hybrid roles. Its small interior, "
                "single bathroom, lack of air conditioning, yard care, and car-oriented setting offset those strengths."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_14",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The condo at 76 Elm Street supports a low-car lifestyle through Jamaica Plain's Orange Line, "
                "bus, bicycle, and walking connections. Its single parking space remains useful for occasional "
                "driving without making the household dependent on a car."
            ),
            "cost_and_property": (
                "The 1926 low-rise condo was remodeled in 2008 and provides 915 square feet with two "
                "bedrooms, one bathroom, and one parking space. It sold for $600,000, is assessed at "
                "$576,000, and has $7,142 in gross annual property tax."
            ),
            "condition_and_features": (
                "The condo was remodeled in 2008 and has forced-air heat with central air conditioning. "
                "Its two-bedroom, 915-square-foot plan works well for a single resident or couple using the "
                "second room as a quiet office, while remaining compact for a family."
            ),
            "amenities_and_services": (
                "JP restaurants and independent shops, groceries, pharmacies, library, health services, "
                "Jamaica Pond, Arboretum, Franklin Park, and transit toward Longwood and downtown."
            ),
            "climate_and_environment": (
                "Jamaica Plain provides more trees and usable urban nature than most central neighborhoods. "
                "That greenery brings pollen and limb cleanup, while snow, ice, humid weather, and localized "
                "drainage remain part of the seasonal environment."
            ),
            "community_and_culture": (
                "Diverse, artsy, civic, LGBTQ+-friendly, family-friendly, active local business scene. "
                "A neighborhood where community identity is part of the attraction."
            ),
            "jobs_and_tradeoffs": (
                "The location provides good access to Longwood healthcare, universities, nonprofits, food and "
                "retail work, while the second bedroom supports remote work. "
                "Parking, central air, parks, and transit are valuable. The one bathroom, modest interior, "
                "and $600,000 cost are the primary limitations."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_15",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The townhouse at 196 Chestnut Avenue has access to bus, Orange Line, and bicycle routes, "
                "while one parking space supports occasional driving. The residential setting is calmer than a downtown tower, "
                "although shared walls and interior stairs reduce privacy and accessibility."
            ),
            "cost_and_property": (
                "This 1988 townhouse condo is unusually spacious for a two-bedroom home, offering 1,493 "
                "square feet but only one bathroom. It includes one parking space and sold for $772,500 in "
                "October 2025. Its assessment is $768,600 and its gross annual property tax is $9,531."
            ),
            "condition_and_features": (
                "Average condition; forced-air heat and central AC. The living area is large enough to carve "
                "out a work zone without losing a bedroom. Its multi-level townhouse layout provides useful "
                "separation between living and working areas but is a poor fit for limited mobility."
            ),
            "amenities_and_services": (
                "Jamaica Plain's neighborhood centers provide food, cafes, pharmacies, libraries, schools, "
                "and health services. Jamaica Pond, the Arboretum, and local parks add outdoor recreation, "
                "while transit connects the home to Longwood and downtown."
            ),
            "climate_and_environment": (
                "Inland greenery and outdoor recreation are advantages. Heat, ice, trees, and localized "
                "heavy-rain flooding are the main environmental tradeoffs."
            ),
            "community_and_culture": (
                "Socially engaged and diverse, with arts, independent businesses, families, queer community, "
                "restaurants and strong access to nature."
            ),
            "jobs_and_tradeoffs": (
                "The large interior, central air, parking, and transit make the townhouse comfortable for a "
                "remote worker, with Longwood healthcare, education, and local service jobs nearby. Its single "
                "bathroom, interior stairs, shared walls, and higher price are the main compromises."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_16",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "60 Sanford Street, Mattapan. Detached and more private than the condo options. Buses, "
                "Mattapan Line and commuter rail serve the area, while the absence of off-street parking "
                "makes the home better suited to a transit-oriented household."
            ),
            "cost_and_property": (
                "The 1900 Colonial was remodeled in 2022 and offers five bedrooms and one and a half "
                "bathrooms across 1,782 square feet, with a 3,470-square-foot lot. It sold for $600,000, "
                "is assessed at $618,300, and carries $7,667 in gross annual property tax."
            ),
            "condition_and_features": (
                "The 1900 Colonial is in average condition after a 2022 remodel. Steam or hot-water heat "
                "serves the house, but there is no central air. Five bedrooms provide extensive family and "
                "office flexibility, while the multi-story layout and single full bathroom reduce convenience."
            ),
            "amenities_and_services": (
                "Local food markets, immigrant-owned restaurants, pharmacies, schools, library, health "
                "centers, parks, Neponset paths, and transit. Longer trip to downtown institutions."
            ),
            "climate_and_environment": (
                "Yard and detached home bring snow, roof, drainage, tree and exterior work. Inland heat and "
                "stormwater matter; direct harbor surge is less central."
            ),
            "community_and_culture": (
                "Vibrant Black, Caribbean and immigrant communities, family networks, churches, local food, "
                "community farming and civic life."
            ),
            "jobs_and_tradeoffs": (
                "Five bedrooms at this price can serve a large or multigenerational household. Access to care, "
                "schools, transit, trades, retail and services. One full bath, no central air or off-street parking, stairs, "
                "older structure and longer commute temper the value."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_17",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The two-family home at 81-83 Westmore Road sits on a residential Mattapan street and includes "
                "two parking spaces. Buses, the Mattapan Line, and commuter rail serve the district, although "
                "car access remains helpful. "
                "Separate households share one property, so privacy is between condo and detached living."
            ),
            "cost_and_property": (
                "Built in 1920, the stacked two-family contains 2,748 square feet with six bedrooms and two "
                "full bathrooms on a 4,550-square-foot lot. The two units suit multigenerational living or "
                "rental use. The property sold for $831,000, is assessed at $738,800, and has $9,161 in "
                "gross annual property tax."
            ),
            "condition_and_features": (
                "The 1920 two-family is in average condition, uses hot-water or steam heat, and has no central "
                "air conditioning. Its two stacked units provide many rooms for family members or offices, "
                "but also double the number of kitchens, living spaces, utilities, and older components that "
                "require ongoing care."
            ),
            "amenities_and_services": (
                "Mattapan Square and local groceries, restaurants, schools, health services, library, parks, "
                "and Neponset recreation. Downtown services are accessible but not a quick walk."
            ),
            "climate_and_environment": (
                "Serving two households increases winter heating and maintenance responsibilities. The property "
                "also faces snow, summer heat without central cooling, mature-tree care, drainage, and localized "
                "river or stormwater exposure."
            ),
            "community_and_culture": (
                "Family-centered Black, Caribbean and immigrant neighborhood with strong churches, local "
                "businesses, food, civic networks, and fewer tourist-oriented amenities."
            ),
            "jobs_and_tradeoffs": (
                "Could combine housing and rent or support extended family. Degree-free work in healthcare "
                "support, schools, transit, construction, warehousing, retail and food service is regionally "
                "accessible. High price, landlord duties, old systems, two baths for six beds, and travel time "
                "are the risks."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_18",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "41 Hawthorne Street #2, Roslindale. Residential and village-oriented. Buses plus commuter "
                "rail provide downtown connections, while one parking space supports driving. The area feels "
                "quieter and less congested than central Boston."
            ),
            "cost_and_property": (
                "The free-standing condo dates to 1966 but was remodeled in 2020. It provides 1,148 square "
                "feet with two bedrooms, one bathroom, and one parking space. It sold for $560,000 in October "
                "2025, is assessed at $593,900, and carries $7,364 in gross annual property tax."
            ),
            "condition_and_features": (
                "The condo is in good condition after a 2020 remodel. It uses hot-water or steam heat and "
                "has no central air conditioning. Its 1,148 square feet comfortably hold an open work area, "
                "while a fully enclosed office would use the second bedroom."
            ),
            "amenities_and_services": (
                "Roslindale Village has groceries, restaurants, cafes, pharmacy, library, farmers market, "
                "community services, and rail connections. The Arboretum and local parks are nearby, while "
                "major hospitals and colleges require a longer transit or car trip."
            ),
            "climate_and_environment": (
                "Leafy surroundings provide attractive outdoor access but also bring tree and limb cleanup. "
                "Snow, ice, site drainage, and humid summers without air conditioning shape seasonal comfort."
            ),
            "community_and_culture": (
                "Friendly and diverse, centered on a real neighborhood business district rather than nightlife. "
                "Families, food, local events, green space, and civic groups."
            ),
            "jobs_and_tradeoffs": (
                "Good assessed condition, remodel record, parking and moderate price. Commuter rail helps office "
                "access; local education, retail, food, care and trade jobs exist. The single bathroom, lack "
                "of air conditioning, and less frequent transit are the main disadvantages."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_19",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "60 Starbird Avenue #2, Roslindale: quiet residential choice. Two parking spaces. Bus and "
                "commuter rail are available but this one tolerates a car-centered routine better than most."
            ),
            "cost_and_property": (
                "Although it has only two bedrooms, this 2019 free-standing condo provides an expansive "
                "1,812 square feet, three full bathrooms, and two parking spaces. It sold for $780,000, "
                "is assessed at $680,000, and has $8,432 in gross annual property tax."
            ),
            "condition_and_features": (
                "The newer condo is in good condition, with forced-air heat, central air conditioning, and "
                "two parking spaces. Its unusually large floor area can hold a dedicated office without "
                "converting a bedroom. The multi-level arrangement creates generous separation but is less "
                "suited to residents with limited mobility."
            ),
            "amenities_and_services": (
                "Village shops and restaurants, library, parks, commuter rail, Arnold Arboretum and other "
                "recreation make the area convenient for daily life. Major hospitals and universities are "
                "reachable by commuter rail, bus, or car but are not immediately nearby."
            ),
            "climate_and_environment": (
                "The 2019 construction and central cooling provide better year-round comfort than the older "
                "homes. Its inland location reduces direct coastal exposure, while snow, mature trees, summer "
                "heat, and localized stormwater remain relevant."
            ),
            "community_and_culture": (
                "Roslindale feels local, welcoming, diverse, green and family-friendly. More neighborhood "
                "events and food than major nightlife or museums."
            ),
            "jobs_and_tradeoffs": (
                "Space, three baths, AC, parking and good condition make a comfortable hybrid-work home. "
                "The $780,000 price is high for only two bedrooms, and transit to downtown takes longer "
                "than from neighborhoods on rapid-transit lines."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_20",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The duplex condo at 4 Robey Street has dense Roxbury city access, with buses nearby and "
                "Orange and Silver Line connections in the larger area. One parking space supports driving, "
                "while the shared construction may transmit sound between homes."
            ),
            "cost_and_property": (
                "Built in 2002, this duplex condo offers 1,356 square feet with three bedrooms, two bathrooms, "
                "and one parking space. It sold for $650,000, is assessed at $467,500, and carries $5,797 "
                "in gross annual property tax."
            ),
            "condition_and_features": (
                "The condo is in good condition and has forced-air heat with central air conditioning. "
                "Three bedrooms can accommodate children or roommates plus a home office. Its two-level "
                "layout creates separation between activities but makes the home less accessible to residents "
                "who avoid stairs."
            ),
            "amenities_and_services": (
                "Local groceries and restaurants, schools, libraries, community health centers, arts groups, "
                "parks, Nubian Square, Franklin Park, Longwood and downtown transit access."
            ),
            "climate_and_environment": (
                "Urban heat is a meaningful Roxbury concern, although central air keeps the interior comfortable. "
                "Heavy rain can create local drainage problems, while winter snow and ice affect the duplex "
                "stairs and neighborhood sidewalks."
            ),
            "community_and_culture": (
                "Historic center of Black Boston with Latino and immigrant communities, arts, churches, civic "
                "organizations, long-term residents, students, and active development debates."
            ),
            "jobs_and_tradeoffs": (
                "The location has strong access to Longwood healthcare and support roles, education, transit, "
                "construction, retail, "
                "food and downtown work. The practical three-bedroom layout, parking, and cooling are balanced "
                "by interior stairs, shared-building responsibilities, urban heat, and street noise."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_21",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The two-family home at 18 Westminster Avenue occupies an unusually large 17,199-square-foot "
                "Roxbury parcel with four parking spaces. Bus and rail connections remain available, but the "
                "parking and detached setting make car ownership easy and provide more privacy than most city homes."
            ),
            "cost_and_property": (
                "The conventional two-family dates to 1890 and provides 3,037 square feet with four bedrooms "
                "and three bathrooms. Its unusually large 17,199-square-foot lot and four parking spaces set "
                "it apart from other city homes. It sold for $1.08 million, is assessed at $1.033 million, "
                "and carries $12,809 in gross annual property tax."
            ),
            "condition_and_features": (
                "The 1890 two-family is in average condition, with steam or hot-water heat and no central "
                "air conditioning. Its age brings a substantial foundation, roof, drainage, wiring, plumbing, "
                "window, and insulation burden. The two units and large interior create excellent office, "
                "rental, or extended-family flexibility, although stairs limit accessibility."
            ),
            "amenities_and_services": (
                "Roxbury provides food, schools, libraries, health centers, parks, arts and civic groups, and "
                "frequent buses. Central hospitals, colleges, and downtown are nearby, although the large "
                "residential parcel is not as immediately walkable as a commercial-center address."
            ),
            "climate_and_environment": (
                "The enormous lot provides exceptional gardening and outdoor potential inside Boston, but it "
                "also creates extensive mowing, tree, runoff, and snow responsibilities. Urban heat and moisture "
                "in the older basement add to the environmental burden."
            ),
            "community_and_culture": (
                "Deep Black cultural and civic history, diverse residents, local arts, faith institutions, "
                "parks, neighborhood business and a strong sense of place."
            ),
            "jobs_and_tradeoffs": (
                "Could house two households, produce rent, support home work, and park four vehicles near a "
                "large job market. But $1.08M plus 1890 upkeep, landlord duties, grounds work, heating and no AC "
                "could overwhelm a buyer who only noticed the square footage."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_22",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "The detached home at 18 Eldora Street is more walkable and transit-friendly than outer Boston, "
                "with Orange Line, Green Line, and bus service in the Roxbury Crossing and Mission Hill area. "
                "Two parking spaces add flexibility, while nearby hospitals and colleges keep the streets active."
            ),
            "cost_and_property": (
                "This detached 1899 Colonial offers 2,149 square feet and four bedrooms but only one bathroom. "
                "It sits on a 3,500-square-foot lot with two parking spaces and sold for $863,000. The house "
                "is assessed at $650,200 and carries $8,062 in gross annual property tax."
            ),
            "condition_and_features": (
                "The 1899 Colonial is in fair condition and has not undergone a recorded remodel. Its older "
                "hot-water or steam system provides heat, while the house has no central cooling. Four bedrooms "
                "create office flexibility, but the single bathroom, interior stairs, and aging structure make "
                "it a renovation-heavy choice."
            ),
            "amenities_and_services": (
                "Northeastern and other colleges, Longwood medical institutions, groceries, pharmacies, parks, "
                "restaurants and central Boston are accessible. Excellent healthcare proximity."
            ),
            "climate_and_environment": (
                "Inland, but urban heat and intense-rain drainage still matter. The old envelope may make both "
                "winter cold and summer heat expensive until improved."
            ),
            "community_and_culture": (
                "Long-term Roxbury and Mission Hill communities mix with students, medical employees, and "
                "university workers. The result is a diverse, busy, institution-centered neighborhood with "
                "strong services and frequent daily activity."
            ),
            "jobs_and_tradeoffs": (
                "Best employment access in the set for healthcare, education, labs, facilities, food, security, "
                "construction and transit. Detached, four beds, yard and parking are compelling. Fair condition, "
                "one bath, no AC, stairs and renovation cost may be dealbreakers."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_23",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "15 I Street #3, South Boston. The walkable location supports a car-free routine using buses, "
                "bicycles, and Red Line connections, and the property has no parking. Commercial and nightlife noise and "
                "shared row-house walls are part of the bargain."
            ),
            "cost_and_property": (
                "The middle-row condo occupies 671 square feet with one bedroom and one bathroom. The building "
                "dates to 1890 and was remodeled in 2004. Its central location commanded a $589,000 sale price, "
                "while the assessment is $561,600 and gross annual property tax is $6,964."
            ),
            "condition_and_features": (
                "The 1890 row-house condo was remodeled in 2004 and uses steam or hot-water heat without "
                "central air conditioning. Its upper-floor, one-bedroom layout offers little storage or "
                "accessibility and places a remote-work desk in the bedroom or main living area."
            ),
            "amenities_and_services": (
                "Food, cafes, pharmacy, library, beaches, waterfront parks, buses, downtown and Seaport jobs. "
                "Strong recreation and everyday access for a compact urban household."
            ),
            "climate_and_environment": (
                "South Boston's coastal setting brings flood, storm-surge, and wind exposure. Humid summers "
                "are harder without air conditioning, while winter ice affects the upper-floor stairs and "
                "sidewalks. Nearby beaches and waterfront parks are a major recreational benefit."
            ),
            "community_and_culture": (
                "Long-standing South Boston traditions alongside younger professionals, restaurants, nightlife, "
                "beaches, sports and fast Seaport change. Social and active."
            ),
            "jobs_and_tradeoffs": (
                "Very good for Seaport, downtown, hospitality, office, construction, facilities and remote work "
                "if little space is needed. The compact home buys location rather than room, with no parking "
                "or central air and meaningful stairs, neighborhood noise, and coastal exposure."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_24",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "188 Corey Street, West Roxbury. This is the large-family suburban-Boston option: detached, "
                "lower density, five parking spaces. Buses and commuter rail exist, but a car is the natural fit. "
                "More privacy and less street noise than the central condos."
            ),
            "cost_and_property": (
                "The 1948 Colonial is designed for a large household, with five bedrooms and three and a "
                "half bathrooms across 2,037 square feet. Its 6,188-square-foot lot includes space for five "
                "vehicles. The house sold for $895,000, is assessed at $882,400, and carries $10,942 in "
                "gross annual property tax."
            ),
            "condition_and_features": (
                "The 1948 Colonial is in average condition and combines hot-water or steam heat with ductless "
                "air conditioning. Its many bedrooms and bathrooms support a large family, guests, and offices, "
                "although the multi-story layout is less accessible. "
                "The 1948 structure carries normal older-house maintenance across its roof, basement, wiring, "
                "windows, insulation, and several ductless cooling zones."
            ),
            "amenities_and_services": (
                "West Roxbury supermarkets, restaurants, schools, pharmacy, library, parks, conservation land, "
                "and commuter rail. Major hospitals, universities and nightlife take a longer trip."
            ),
            "climate_and_environment": (
                "Greener inland setting with outdoor room, plus leaves, lawn, trees, snow and exterior work. "
                "It has less direct coastal exposure than waterfront neighborhoods, although heavy rain can "
                "still create drainage and basement-moisture problems."
            ),
            "community_and_culture": (
                "West Roxbury feels friendly, residential, family-oriented, and relatively suburban. Local "
                "businesses, civic groups, and parks shape community life, while nightlife and cultural venues "
                "are less concentrated than in Jamaica Plain or downtown."
            ),
            "jobs_and_tradeoffs": (
                "Five bedrooms, three and a half bathrooms, cooling, and abundant parking make remote work and "
                "large-family life comfortable. Commuter rail serves downtown, while local care, school, trade, "
                "and service jobs are available. The high price, stairs, car dependence, and full house-and-yard "
                "maintenance are the cost of that space."
            ),
        },
    ),
    SurveyResponse(
        entity_id="boston_house_25",
        entity_type="house",
        survey_id="house_survey",
        answers={
            "location_and_transportation": (
                "57 Rockland Street, West Roxbury, is quiet, detached, and the most private outdoor setting "
                "in the group. Three parking spaces make driving convenient, while neighborhood bus and "
                "commuter-rail options provide an alternative for downtown trips."
            ),
            "cost_and_property": (
                "The Cape-style house dates to 1900 and was remodeled in 2024. Its 1,391-square-foot interior "
                "contains three bedrooms and one bathroom, while the unusually large 11,250-square-foot lot "
                "provides substantial outdoor space and three parking spaces. It sold for $920,000, is assessed "
                "at $554,200, and carries $6,872 in gross annual property tax."
            ),
            "condition_and_features": (
                "The Cape is in good condition after a 2024 remodel, although its underlying structure dates "
                "to 1900. Hot-water or steam heat serves the house, which lacks central air conditioning. "
                "Three bedrooms allow an office only by sharing or sacrificing a sleeping room, while the "
                "Cape layout provides some first-floor living but still includes stairs."
            ),
            "amenities_and_services": (
                "Local groceries, restaurants, schools, pharmacy, library, parks, conservation areas and commuter "
                "rail. It prioritizes land and quiet over immediate hospitals, universities, museums or nightlife."
            ),
            "climate_and_environment": (
                "The expansive lot offers the best gardening and outdoor play potential in the set, along with "
                "the largest burden of lawn, tree, leaf, snow, runoff, and exterior maintenance. Its inland "
                "position reduces coastal exposure, but heavy rain creates more drainage responsibility."
            ),
            "community_and_culture": (
                "Quiet, suburban, family-oriented Boston neighborhood. Community groups, parks and local shopping; "
                "less diversity of late-night entertainment than central districts."
            ),
            "jobs_and_tradeoffs": (
                "The quiet setting, large lot, and three bedrooms suit a privacy-seeking hybrid worker or family. "
                "Commuter access connects to downtown, while schools, healthcare support, retail, and trade work "
                "are available locally. The high price buys only one bathroom and 1,391 interior square feet, "
                "with no central air, an old structure, car use, and major yard work."
            ),
        },
    ),
]


__all__ = ["house_survey", "house_responses"]
