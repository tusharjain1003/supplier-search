from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .data_loader import get_supplier_profile, load_supplier_profiles
from .explanations import evidence_summary
from .query_parser import clarification_questions, parse_query
from .ranking import rank_suppliers
from .schemas import SearchRequest, SearchResponse, SupplierDetailResponse


app = FastAPI(
    title="Supplier Search",
    version="0.1.0",
    description="Evidence-backed supplier search and ranking prototype.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    parsed = parse_query(request.query)
    ranked = rank_suppliers(load_supplier_profiles(), parsed, request.weights or {})
    results = ranked["results"]

    clarifications = clarification_questions(parsed)
    status = "ok"
    message = None
    fallback_suggestions = []
    if clarifications:
        status = "needs_clarification"
        message = "The query is missing one or more key procurement criteria; partial results are shown."
    if not results:
        status = "no_results"
        message = "No suppliers matched the available dataset."
        fallback_suggestions = [
            "Relax ISO certification requirement",
            "Expand country filter",
            "Allow buyer evidence older than 12 months",
        ]

    return {
        "status": status,
        "parsed_query": {
            "category": parsed.category,
            "countries": parsed.countries,
            "requires_iso": parsed.requires_iso,
            "buyer_type": parsed.buyer_type,
            "shipment_window_months": parsed.shipment_window_months,
            "compliance_required": parsed.compliance_required,
        },
        "normalized_weights": ranked["weights"],
        "results": results,
        "message": message,
        "suggested_clarifications": clarifications,
        "fallback_suggestions": fallback_suggestions,
    }


@app.get("/suppliers/{supplier_id}", response_model=SupplierDetailResponse)
def supplier_detail(supplier_id: str):
    try:
        profile = get_supplier_profile(supplier_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Supplier not found") from exc

    return {
        "supplier_id": profile.supplier_id,
        "canonical_name": profile.canonical_name,
        "aliases": profile.aliases,
        "country": profile.country,
        "website": profile.website,
        "product_categories": profile.product_categories,
        "entity_resolution": {
            "aliases": profile.entity_resolution.aliases,
            "linked_records": profile.entity_resolution.linked_records,
            "resolution_confidence": profile.entity_resolution.resolution_confidence,
            "reason": profile.entity_resolution.reason,
            "candidate_matches": profile.entity_resolution.candidate_matches,
        },
        "evidence": evidence_summary(profile.evidence, limit=100),
    }

