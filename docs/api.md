# API

## GET /health

Response:

```json
{
  "status": "ok"
}
```

## POST /search

Request:

```json
{
  "query": "Find ISO-certified copper cable suppliers in Vietnam, India, or China who have evidence of supplying to large US companies in the last 12 months and have no compliance concerns.",
  "weights": {
    "category": 0.25,
    "location": 0.15,
    "iso_certification": 0.20,
    "buyer_evidence": 0.25,
    "compliance": 0.15
  }
}
```

Response fields:

- `status`: `ok`, `needs_clarification`, or `no_results`.
- `parsed_query`: structured criteria extracted from the natural language query.
- `normalized_weights`: weights after automatic normalization.
- `results`: ranked suppliers with match, confidence, freshness, final score, explanation, evidence, and weaknesses.
- `match_score`, `confidence_score`, `freshness_score`, and `final_score` are display scores on a 0-100 scale.
- `matched_criteria` contains per-criterion component scores on a 0-1 scale so the weighted formula remains easy to audit.
- `confidence_components` contains the four 0-1 confidence inputs: source reliability, cross-source confirmation, freshness, and contradiction.

## GET /suppliers/{supplier_id}

Returns canonical profile details:

- aliases and linked records
- entity resolution confidence
- product categories
- all evidence records with source reliability and timestamps
