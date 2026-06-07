from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass
class SupplierRecord:
    supplier_id: str
    supplier_name: str
    canonical_name: str
    country: str
    website: str
    product_categories: List[str]
    created_at: date


@dataclass
class EvidenceRecord:
    evidence_id: str
    supplier_id: str
    claim_type: str
    claim_value: str
    source_type: str
    source_name: str
    source_reliability: float
    evidence_date: date
    confidence: float
    notes: str


@dataclass
class EntityResolution:
    aliases: List[str]
    linked_records: List[str]
    resolution_confidence: float
    reason: str
    candidate_matches: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class SupplierProfile:
    supplier_id: str
    canonical_name: str
    country: str
    website: str
    product_categories: List[str]
    records: List[SupplierRecord]
    aliases: List[str]
    evidence: List[EvidenceRecord]
    entity_resolution: EntityResolution


@dataclass
class ParsedQuery:
    category: Optional[str]
    countries: List[str]
    requires_iso: bool
    buyer_type: Optional[str]
    shipment_window_months: Optional[int]
    compliance_required: bool
    raw_query: str

