from typing import Dict, List

from .models import EvidenceRecord, SupplierProfile


def confidence_label(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.6:
        return "medium"
    return "low"


def evidence_summary(records: List[EvidenceRecord], limit: int = 4) -> List[Dict[str, str]]:
    sorted_records = sorted(records, key=lambda item: (item.source_reliability, item.evidence_date), reverse=True)
    return [
        {
            "evidence_id": record.evidence_id,
            "claim": record.claim_value,
            "claim_type": record.claim_type,
            "source": record.source_name,
            "source_type": record.source_type,
            "source_reliability": record.source_reliability,
            "confidence": confidence_label(record.confidence),
            "timestamp": record.evidence_date.isoformat(),
            "notes": record.notes,
        }
        for record in sorted_records[:limit]
    ]


def weaknesses(profile: SupplierProfile, components: Dict[str, float]) -> List[str]:
    notes: List[str] = []
    if components["category"] < 1.0:
        notes.append("Product category is related or weak rather than an exact copper cable match.")
    if components["location"] < 1.0:
        notes.append("Supplier is outside the requested countries.")
    if components["iso_certification"] == 0.5:
        notes.append("ISO certification is only self-claimed on the supplier website.")
    elif components["iso_certification"] == 0.2:
        notes.append("ISO evidence is expired.")
    elif components["iso_certification"] == 0:
        notes.append("No ISO certification evidence was found.")
    if components["buyer_evidence"] == 0.4:
        notes.append("Shipment evidence exists but is older than the requested time window.")
    elif components["buyer_evidence"] == 0.3:
        notes.append("Buyer evidence is self-claimed and not backed by trade data.")
    elif components["buyer_evidence"] == 0:
        notes.append("No large US buyer evidence was found.")
    if components["compliance"] == 0:
        notes.append("Active compliance concern is present.")
    elif components["compliance"] == 0.5:
        notes.append("Compliance status is unknown or weakly evidenced.")
    if not profile.evidence:
        notes.append("No supporting evidence records are available.")
    return notes


def rank_explanation(profile: SupplierProfile, components: Dict[str, float], rank: int) -> str:
    strengths: List[str] = []
    if components["category"] == 1.0:
        strengths.append("matches the requested copper cable category")
    if components["location"] == 1.0:
        strengths.append(f"is located in {profile.country}")
    if components["iso_certification"] == 1.0:
        strengths.append("has active ISO evidence from a certification database")
    elif components["iso_certification"] == 0.5:
        strengths.append("has ISO evidence only from its website")
    if components["buyer_evidence"] == 1.0:
        strengths.append("has recent trade evidence to a large US buyer")
    elif components["buyer_evidence"] == 0.4:
        strengths.append("has older trade evidence to a large US buyer")
    if components["compliance"] == 1.0:
        strengths.append("has no compliance flags in the compliance database")

    if not strengths:
        return f"Ranked #{rank} because it has limited evidence against the requested criteria."
    return f"Ranked #{rank} because this supplier " + ", ".join(strengths) + "."

