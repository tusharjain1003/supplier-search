from datetime import date
from typing import Dict, Iterable, List, Tuple

from .config import DEFAULT_AS_OF_DATE, DEFAULT_WEIGHTS
from .models import EvidenceRecord, ParsedQuery, SupplierProfile


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    merged = DEFAULT_WEIGHTS.copy()
    for key, value in (weights or {}).items():
        if key in merged and value is not None and value >= 0:
            merged[key] = float(value)
    total = sum(merged.values())
    if total <= 0:
        return DEFAULT_WEIGHTS.copy()
    return {key: value / total for key, value in merged.items()}


def months_old(evidence_date: date, as_of: date = DEFAULT_AS_OF_DATE) -> int:
    return max(0, (as_of.year - evidence_date.year) * 12 + as_of.month - evidence_date.month)


def freshness_for_evidence(evidence: EvidenceRecord, as_of: date = DEFAULT_AS_OF_DATE) -> float:
    age_months = months_old(evidence.evidence_date, as_of)
    value = evidence.claim_value.lower()
    if "expired" in value:
        return 0.0
    if age_months <= 12:
        return 1.0
    if age_months <= 24:
        return 0.7
    return 0.4


def _claim_evidence(profile: SupplierProfile, claim_type: str) -> List[EvidenceRecord]:
    return [record for record in profile.evidence if record.claim_type == claim_type]


def _best_iso_score(evidence: Iterable[EvidenceRecord]) -> float:
    score = 0.0
    for record in evidence:
        value = record.claim_value.lower()
        if "expired" in value:
            score = max(score, 0.2)
        elif "active" in value and record.source_type == "certification_database":
            score = max(score, 1.0)
        elif "active" in value and record.source_type == "company_website":
            score = max(score, 0.5)
    return score


def _best_buyer_score(evidence: Iterable[EvidenceRecord], window_months: int, as_of: date) -> float:
    score = 0.0
    for record in evidence:
        if record.claim_type == "trade_shipment":
            score = max(score, 1.0 if months_old(record.evidence_date, as_of) <= window_months else 0.4)
        elif record.claim_type == "website_claim":
            score = max(score, 0.3)
    return score


def _compliance_score(evidence: Iterable[EvidenceRecord]) -> float:
    compliance = list(evidence)
    if not compliance:
        return 0.5
    for item in compliance:
        value = item.claim_value.lower()
        has_risk_language = "concern" in value or "flag" in value
        explicitly_clear = (
            value.startswith("no ")
            or "no compliance" in value
            or "no material" in value
        )
        if has_risk_language and not explicitly_clear:
            return 0.0
    if any("no compliance" in item.claim_value.lower() or "no " in item.claim_value.lower() for item in compliance):
        return 1.0
    return 0.5


def compute_match_components(
    profile: SupplierProfile,
    parsed_query: ParsedQuery,
    as_of: date = DEFAULT_AS_OF_DATE,
) -> Dict[str, float]:
    category_score = 0.0
    if parsed_query.category:
        if parsed_query.category in profile.product_categories:
            category_score = 1.0
        elif any("cable" in category for category in profile.product_categories):
            category_score = 0.7
    else:
        category_score = 0.5

    location_score = 1.0 if not parsed_query.countries or profile.country in parsed_query.countries else 0.0
    iso_score = _best_iso_score(_claim_evidence(profile, "iso_certification")) if parsed_query.requires_iso else 0.5
    buyer_score = _best_buyer_score(
        [record for record in profile.evidence if record.claim_type in {"trade_shipment", "website_claim"}],
        parsed_query.shipment_window_months or 12,
        as_of,
    ) if parsed_query.buyer_type else 0.5
    compliance_score = _compliance_score(_claim_evidence(profile, "compliance")) if parsed_query.compliance_required else 0.5

    return {
        "category": round(category_score, 3),
        "location": round(location_score, 3),
        "iso_certification": round(iso_score, 3),
        "buyer_evidence": round(buyer_score, 3),
        "compliance": round(compliance_score, 3),
    }


def compute_weighted_match(components: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(components[key] * weights[key] for key in DEFAULT_WEIGHTS)


def compute_confidence(profile: SupplierProfile, as_of: date = DEFAULT_AS_OF_DATE) -> Tuple[float, Dict[str, float]]:
    if not profile.evidence:
        return 0.2, {
            "source_reliability": 0.2,
            "cross_source_confirmation": 0.0,
            "freshness": 0.0,
            "contradiction": 0.5,
        }

    source_reliability = sum(record.source_reliability for record in profile.evidence) / len(profile.evidence)
    source_types = {record.source_type for record in profile.evidence}
    if len(source_types) >= 3:
        cross_source = 1.0
    elif len(source_types) == 2:
        cross_source = 0.7
    elif "company_website" in source_types:
        cross_source = 0.2
    else:
        cross_source = 0.4

    freshness = sum(freshness_for_evidence(record, as_of) for record in profile.evidence) / len(profile.evidence)
    values = " ".join(record.claim_value.lower() for record in profile.evidence)
    contradiction = 0.0 if "expired" in values or "active customs" in values else 1.0
    if not _claim_evidence(profile, "iso_certification") or not _claim_evidence(profile, "compliance"):
        contradiction = min(contradiction, 0.5)

    confidence = (
        0.40 * source_reliability
        + 0.25 * cross_source
        + 0.20 * freshness
        + 0.15 * contradiction
    )
    components = {
        "source_reliability": source_reliability,
        "cross_source_confirmation": cross_source,
        "freshness": freshness,
        "contradiction": contradiction,
    }
    return round(confidence, 4), {key: round(value, 4) for key, value in components.items()}


def compute_freshness(profile: SupplierProfile, as_of: date = DEFAULT_AS_OF_DATE) -> float:
    key_evidence = [
        record
        for record in profile.evidence
        if record.claim_type in {"iso_certification", "trade_shipment", "compliance"}
    ]
    if not key_evidence:
        return 0.0
    return round(sum(freshness_for_evidence(record, as_of) for record in key_evidence) / len(key_evidence), 4)
