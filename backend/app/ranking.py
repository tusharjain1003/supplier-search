from datetime import date
from typing import Dict, List

from .config import DEFAULT_AS_OF_DATE
from .explanations import evidence_summary, rank_explanation, weaknesses
from .models import ParsedQuery, SupplierProfile
from .scoring import compute_confidence, compute_freshness, compute_match_components, compute_weighted_match, normalize_weights


def rank_suppliers(
    profiles: List[SupplierProfile],
    parsed_query: ParsedQuery,
    weights: Dict[str, float],
    as_of: date = DEFAULT_AS_OF_DATE,
) -> Dict[str, object]:
    normalized_weights = normalize_weights(weights)
    scored: List[Dict[str, object]] = []
    for profile in profiles:
        components = compute_match_components(profile, parsed_query, as_of)
        match = compute_weighted_match(components, normalized_weights)
        confidence, confidence_components = compute_confidence(profile, as_of)
        freshness = compute_freshness(profile, as_of)
        final = 0.65 * match + 0.25 * confidence + 0.10 * freshness
        scored.append(
            {
                "profile": profile,
                "components": components,
                "match_score": match,
                "confidence_score": confidence,
                "confidence_components": confidence_components,
                "freshness_score": freshness,
                "final_score": final,
            }
        )

    scored.sort(key=lambda item: item["final_score"], reverse=True)
    results: List[Dict[str, object]] = []
    for rank, item in enumerate(scored, start=1):
        profile = item["profile"]
        components = item["components"]
        results.append(
            {
                "supplier_id": profile.supplier_id,
                "supplier_name": profile.canonical_name,
                "country": profile.country,
                "rank": rank,
                "match_score": round(item["match_score"] * 100, 1),
                "confidence_score": round(item["confidence_score"] * 100, 1),
                "freshness_score": round(item["freshness_score"] * 100, 1),
                "final_score": round(item["final_score"] * 100, 1),
                "detail_url": f"/suppliers/{profile.supplier_id}",
                "matched_criteria": components,
                "confidence_components": item["confidence_components"],
                "explanation": rank_explanation(profile, components, rank),
                "evidence": evidence_summary(profile.evidence),
                "weaknesses": weaknesses(profile, components),
            }
        )
    return {"weights": normalized_weights, "results": results}

