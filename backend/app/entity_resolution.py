import re
from difflib import SequenceMatcher
from typing import Dict, List

from .models import EntityResolution, SupplierRecord


LEGAL_SUFFIXES = {
    "ltd",
    "limited",
    "llc",
    "inc",
    "pvt",
    "private",
    "co",
    "company",
    "group",
    "corp",
    "corporation",
    "manufacturing",
}


def normalize_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    tokens = [token for token in cleaned.split() if token not in LEGAL_SUFFIXES]
    return " ".join(tokens)


def name_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_name(left), normalize_name(right)).ratio()


def build_entity_resolution(
    records: List[SupplierRecord],
    aliases: List[str],
    candidate_matches: List[Dict[str, str]] = None,
) -> EntityResolution:
    linked_records = sorted({record.supplier_name for record in records})
    normalized_names = [normalize_name(name) for name in linked_records + aliases]
    unique_normalized = {name for name in normalized_names if name}
    same_country = len({record.country for record in records}) == 1
    overlapping_category = bool(
        set(records[0].product_categories).intersection(
            *(set(record.product_categories) for record in records[1:])
        )
    ) if len(records) > 1 else True

    if len(records) > 1:
        confidence = 0.86
        if same_country:
            confidence += 0.04
        if overlapping_category:
            confidence += 0.04
        if len(unique_normalized) < len(normalized_names):
            confidence += 0.03
        reason = "Linked by shared canonical name, same country, overlapping product category, and matching alias evidence."
    else:
        confidence = 0.74
        reason = "Single supplier record; aliases retained but no duplicate merge was required."

    return EntityResolution(
        aliases=sorted(set(aliases)),
        linked_records=linked_records,
        resolution_confidence=round(min(confidence, 0.98), 2),
        reason=reason,
        candidate_matches=candidate_matches or [],
    )


def find_candidate_matches(records: List[SupplierRecord], threshold: float = 0.55) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            if left.country != right.country:
                continue
            if not set(left.product_categories).intersection(right.product_categories):
                continue
            score = name_similarity(left.supplier_name, right.supplier_name)
            if score >= threshold and left.canonical_name != right.canonical_name:
                candidates.append(
                    {
                        "left_supplier_id": left.supplier_id,
                        "left_supplier_name": left.supplier_name,
                        "right_supplier_id": right.supplier_id,
                        "right_supplier_name": right.supplier_name,
                        "similarity": f"{score:.2f}",
                        "reason": "Medium name similarity, same country, and overlapping product category; candidate only, not auto-merged.",
                    }
                )
    return candidates
