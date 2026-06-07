from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .config import DEFAULT_WEIGHTS


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    weights: Optional[Dict[str, float]] = None


class ParsedQueryResponse(BaseModel):
    category: Optional[str]
    countries: List[str]
    requires_iso: bool
    buyer_type: Optional[str]
    shipment_window_months: Optional[int]
    compliance_required: bool


class EvidenceResponse(BaseModel):
    evidence_id: Optional[str] = None
    claim: str
    claim_type: Optional[str] = None
    source: str
    source_type: Optional[str] = None
    source_reliability: Optional[float] = None
    confidence: str
    timestamp: str
    notes: Optional[str] = None


class SearchResult(BaseModel):
    supplier_id: str
    supplier_name: str
    country: str
    rank: int
    match_score: float
    confidence_score: float
    freshness_score: float
    final_score: float
    detail_url: str
    matched_criteria: Dict[str, float]
    confidence_components: Dict[str, float]
    explanation: str
    evidence: List[EvidenceResponse]
    weaknesses: List[str]


class SearchResponse(BaseModel):
    status: str
    parsed_query: ParsedQueryResponse
    normalized_weights: Dict[str, float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    results: List[SearchResult]
    message: Optional[str] = None
    suggested_clarifications: List[str] = []
    fallback_suggestions: List[str] = []


class EntityResolutionResponse(BaseModel):
    aliases: List[str]
    linked_records: List[str]
    resolution_confidence: float
    reason: str
    candidate_matches: List[Dict[str, str]]


class SupplierDetailResponse(BaseModel):
    supplier_id: str
    canonical_name: str
    aliases: List[str]
    country: str
    website: str
    product_categories: List[str]
    entity_resolution: EntityResolutionResponse
    evidence: List[EvidenceResponse]
