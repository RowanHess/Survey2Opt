# Boston matching + tone ablation data

## Experiment inputs

| File | Role |
|------|------|
| `house_data.py` | House survey + 25 Boston listing responses |
| `person_survey_responses.json` | 25 person survey responses (canonical tone) |
| `tone_ablations.json` | Soft / neutral / harsh person variants |
| `boston_housing.py` | Loader for matching and tone conditions |
| `__init__.py` | Package marker |

## Ground truth (synthetic latent world)

| File | Role |
|------|------|
| `weights_ground_truth.json` | Person×house compatibility weights |
| `matching_ground_truth.json` | Max-weight matching on those weights |
| `people_latents.json` | Numeric person prefs/constraints/tone used to score |
| `houses_latents.json` | Numeric synthetic house facts used to score |

These GT files use IDs `person_01`…`person_25` and `house_01`…`house_15` (contiguous). Ten houses were removed so the ground-truth matching covers **every remaining house** (25 people × 15 houses; 10 people unmatched). The rename map from pre-trim IDs is stored in `matching_ground_truth.json` / `houses_latents.json` as `house_id_rename`. They are for evaluating recovery against known prefs (and tone ablations on the same people), not as labels for the Boston assessment listings in `house_data.py`.

## Matching

```python
from data.boston_housing import (
    house_survey,
    person_survey,
    all_responses,
    boston_guidance,
)
```

```bash
export PARLEY_API_KEY=...
python examples/boston_matching.py
```

## Tone ablation

```python
from data.boston_housing import (
    house_responses,
    load_tone_ablation_responses,
    boston_guidance,
)

person_soft = load_tone_ablation_responses("soft")  # or "neutral" / "harsh"
responses = list(house_responses) + person_soft
```
