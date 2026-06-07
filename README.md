# Supplier Search

Evidence-backed supplier search prototype that converts a natural language procurement request into structured criteria, resolves noisy supplier records into canonical profiles, scores evidence confidence separately from business relevance, and returns ranked supplier recommendations with explanations.

## What It Demonstrates

- Natural language query parsing into structured supplier criteria.
- Mock supplier dataset with duplicates, stale evidence, expired ISO records, website-only claims, and compliance flags.
- Supplier normalization and alias/entity resolution.
- Deterministic confidence scoring based on source reliability, cross-source confirmation, freshness, and contradictions.
- User-adjustable ranking weights.
- Explainable API and Streamlit UI.

## Project Structure

```text
backend/
  app/                  FastAPI app and deterministic ranking logic
  data/                 Mock supplier, alias, evidence, and source reliability CSVs
  tests/                Unit and API tests
frontend/
  streamlit_app.py      Lightweight UI
docs/
  technical_note.md     One-page architecture and scoring note
  api.md                API examples
  assumptions.md        Scope, limitations, and production extensions
```

## Setup

```bash
cd /Users/tusharjain/Downloads/shyva_assignment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Run API

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Run UI

```bash
streamlit run frontend/streamlit_app.py
```

## Run Tests

```bash
PYTHONPATH=backend pytest backend/tests -q
```

## Sample API Request

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find ISO-certified copper cable suppliers in Vietnam, India, or China who have evidence of supplying to large US companies in the last 12 months and have no compliance concerns.",
    "weights": {
      "category": 0.25,
      "location": 0.15,
      "iso_certification": 0.20,
      "buyer_evidence": 0.25,
      "compliance": 0.15
    }
  }'
```

## Design Boundary

LLMs are intentionally not required for this prototype. Query parsing is deterministic, and ranking, confidence scoring, ISO validity, compliance handling, freshness, and entity resolution are deterministic and auditable. A production version could add an LLM parser with strict JSON validation and fallback to the deterministic parser.

