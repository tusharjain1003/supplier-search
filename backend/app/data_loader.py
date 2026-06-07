import csv
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List

from .config import DATA_DIR
from .entity_resolution import build_entity_resolution, find_candidate_matches
from .models import EvidenceRecord, SupplierProfile, SupplierRecord


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _split_categories(value: str) -> List[str]:
    return [item.strip().lower() for item in value.split(";") if item.strip()]


def _read_csv(path: Path) -> Iterable[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


@lru_cache(maxsize=1)
def load_supplier_records() -> List[SupplierRecord]:
    records: List[SupplierRecord] = []
    for row in _read_csv(DATA_DIR / "suppliers.csv"):
        records.append(
            SupplierRecord(
                supplier_id=row["supplier_id"],
                supplier_name=row["supplier_name"],
                canonical_name=row["canonical_name"],
                country=row["country"],
                website=row["website"],
                product_categories=_split_categories(row["product_categories"]),
                created_at=_parse_date(row["created_at"]),
            )
        )
    return records


@lru_cache(maxsize=1)
def load_aliases() -> Dict[str, List[str]]:
    aliases: Dict[str, List[str]] = {}
    for row in _read_csv(DATA_DIR / "supplier_aliases.csv"):
        aliases.setdefault(row["supplier_id"], []).append(row["alias_name"])
    return aliases


@lru_cache(maxsize=1)
def load_source_reliability() -> Dict[str, float]:
    return {
        row["source_type"]: float(row["reliability_score"])
        for row in _read_csv(DATA_DIR / "source_reliability.csv")
    }


@lru_cache(maxsize=1)
def load_evidence_records() -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    reliability_by_source = load_source_reliability()
    for row in _read_csv(DATA_DIR / "evidence.csv"):
        source_type = row["source_type"]
        if source_type not in reliability_by_source:
            raise ValueError(f"Unknown source_type in evidence.csv: {source_type}")
        records.append(
            EvidenceRecord(
                evidence_id=row["evidence_id"],
                supplier_id=row["supplier_id"],
                claim_type=row["claim_type"],
                claim_value=row["claim_value"],
                source_type=source_type,
                source_name=row["source_name"],
                source_reliability=reliability_by_source[source_type],
                evidence_date=_parse_date(row["evidence_date"]),
                confidence=float(row["confidence"]),
                notes=row["notes"],
            )
        )
    return records


@lru_cache(maxsize=1)
def load_supplier_profiles() -> List[SupplierProfile]:
    supplier_records = load_supplier_records()
    evidence_records = load_evidence_records()
    aliases_by_supplier = load_aliases()
    candidate_matches = find_candidate_matches(supplier_records)

    records_by_canonical: Dict[str, List[SupplierRecord]] = {}
    for record in supplier_records:
        records_by_canonical.setdefault(record.canonical_name, []).append(record)

    evidence_by_supplier: Dict[str, List[EvidenceRecord]] = {}
    for evidence in evidence_records:
        evidence_by_supplier.setdefault(evidence.supplier_id, []).append(evidence)

    profiles: List[SupplierProfile] = []
    for canonical_name, records in records_by_canonical.items():
        primary = sorted(records, key=lambda item: item.supplier_id)[0]
        record_ids = {record.supplier_id for record in records}
        profile_evidence = [
            evidence
            for supplier_id in record_ids
            for evidence in evidence_by_supplier.get(supplier_id, [])
        ]
        product_categories = sorted(
            {category for record in records for category in record.product_categories}
        )
        aliases = sorted(
            {
                alias
                for record in records
                for alias in aliases_by_supplier.get(record.supplier_id, [])
            }
            | {record.supplier_name for record in records}
        )
        record_ids = {record.supplier_id for record in records}
        profile_candidates = [
            candidate
            for candidate in candidate_matches
            if candidate["left_supplier_id"] in record_ids
            or candidate["right_supplier_id"] in record_ids
        ]
        profiles.append(
            SupplierProfile(
                supplier_id=primary.supplier_id,
                canonical_name=canonical_name,
                country=primary.country,
                website=primary.website,
                product_categories=product_categories,
                records=records,
                aliases=aliases,
                evidence=profile_evidence,
                entity_resolution=build_entity_resolution(records, aliases, profile_candidates),
            )
        )
    return sorted(profiles, key=lambda item: item.canonical_name)


def get_supplier_profile(supplier_id: str) -> SupplierProfile:
    for profile in load_supplier_profiles():
        if supplier_id == profile.supplier_id or supplier_id in {r.supplier_id for r in profile.records}:
            return profile
    raise KeyError(supplier_id)
