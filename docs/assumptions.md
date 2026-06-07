# Assumptions, Limitations, And Future Improvements

## Assumptions

- The dataset is intentionally small and mock-only.
- `large US companies` are represented by mock buyer names in trade evidence notes.
- Current date is fixed at 2026-06-07 so freshness scores are repeatable.
- Country matching is exact.
- Product matching is simple category matching with partial credit for related cable categories.

## Limitations

- No paid trade, certification, compliance, or corporate registry data is used.
- Entity resolution is deliberately simple and should not be used for real supplier diligence.
- The compliance model only distinguishes no flag, unknown, and active concern.
- Website-only claims are retained as evidence but are penalized.
- No authentication, RBAC, source crawling, or production persistence is included.

## Future Improvements

- Add an LLM parser with strict schema validation and deterministic fallback.
- Add source ingestion jobs with raw snapshot retention.
- Add stronger entity identifiers such as registration IDs, tax IDs, domains, addresses, and certification IDs.
- Add human review workflows for medium-confidence entity merges.
- Add faceted search, semantic retrieval, and audit trails for score changes.
- Tune scoring weights from buyer feedback and analyst review outcomes.

