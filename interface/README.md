# Local housing matching interface

This folder contains a lightweight Flask app that lets a few users fill out a short home-preference survey and then runs the existing `surveyopt` decision pipeline against a curated set of houses.

## Start the app

From the repository root:

```bash
source .venv/bin/activate
python interface/app.py
```

Then open http://127.0.0.1:5000 in a browser.

## Configure the model API

The server expects either `PARLEY_API_KEY` or `OPENAI_API_KEY` to be set in the environment.

```bash
export PARLEY_API_KEY="..."
```

Optional:

```bash
export PARLEY_BASE_URL="https://parley.api.mit.edu/v1"
export PARLEY_SMART_MODEL="openai/gpt-5.6-terra"
```

## Replace the house inventory

Edit `interface/data/houses.json` with your own listings. Each entry should include:

- `id`
- `address`
- `city`
- `state`
- `price`
- `bedrooms`
- `bathrooms`
- `sqft`
- `style`
- `lat`
- `lng`
- `tags`
- `description`

## Run artifacts

This interface sets the pipeline artifact root to `interface/runs`, so each matching session writes detailed run history, summaries, and candidate JSON under that directory.
