# Technical Note

## Problem Understanding

The prototype demonstrates how an AI-native supplier search system can turn a procurement request into ranked supplier recommendations without treating the model as the trust engine. The important separation is between business relevance, such as product and country fit, and evidence confidence, such as whether claims are verified by reliable, fresh, independent sources.

## Architecture

The app uses a small FastAPI backend with a Streamlit UI. A deterministic query parser extracts category, countries, ISO requirement, buyer evidence, shipment window, and compliance requirement. CSV files provide suppliers, aliases, evidence records, and source reliability scores. The backend loads records into canonical supplier profiles, aggregates evidence across aliases, computes match and confidence scores, ranks suppliers, and generates explanations. Name similarity uses Python's standard-library `difflib.SequenceMatcher`; a production system could swap in `rapidfuzz` or a richer entity-resolution service.

## Data Model

Suppliers are stored separately from evidence. Evidence records include `claim_type`, `claim_value`, `source_type`, `source_name`, `evidence_date`, confidence, and notes. Source reliability is loaded from `source_reliability.csv` so source trust scores have one authoritative home. This avoids flattening trust-sensitive facts into fields like `iso_certified=true` without provenance.

## Ranking Formula

User weights are normalized automatically. The weighted business match score is:

```text
match_score =
  category_weight * category_match
+ location_weight * location_match
+ iso_weight * iso_match
+ buyer_evidence_weight * buyer_evidence_match
+ compliance_weight * compliance_match
```

The final score is:

```text
final_score = 0.65 * match_score + 0.25 * confidence_score + 0.10 * freshness_score
```

Scores are displayed on a 0-100 scale.

## Confidence Scoring

Confidence is separate from relevance:

```text
confidence_score =
  0.40 * source_reliability
+ 0.25 * cross_source_confirmation
+ 0.20 * freshness
+ 0.15 * contradiction
```

Official certification, trade, and compliance databases are more reliable than company websites. Recent evidence scores higher than stale evidence. Expired ISO records and active compliance concerns reduce trust.

These weights are hand-tuned prototype defaults, not learned truth. In production they should be configurable by source type and industry segment, and could be tuned from human review feedback and buyer preference pilots.

## LLM vs Deterministic Logic

This prototype does not need an LLM. An LLM could be added only for natural language query parsing and optional explanation drafting, with Pydantic validation and deterministic fallback. Ranking, confidence scoring, compliance decisions, ISO validity, shipment freshness, and entity merge decisions remain deterministic.

## Assumptions And Limitations

The dataset is mock data. Entity resolution uses canonical labels, normalized names, country, aliases, and product overlap; it does not solve subsidiaries, multilingual names, registration IDs, or ownership structures. Compliance coverage is intentionally narrow. The score weights are hand-tuned for clarity and should be configurable in production.

## Production Scaling

A production system would store raw source snapshots in object storage, canonical entities and evidence metadata in Postgres, use OpenSearch for faceted search, add vector retrieval for semantic matching, and run ingestion/enrichment jobs through queues. Entity resolution should use strong identifiers such as tax IDs, registration IDs, certification IDs, websites, addresses, and emails, with human review for medium-confidence merges.
