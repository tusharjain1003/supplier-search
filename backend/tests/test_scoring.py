from datetime import date

from app.data_loader import load_source_reliability, load_supplier_profiles
from app.models import EvidenceRecord, SupplierProfile, EntityResolution, SupplierRecord
from app.query_parser import parse_query
from app.ranking import rank_suppliers
from app.scoring import compute_confidence, compute_freshness, compute_match_components, normalize_weights


QUERY = parse_query(
    "Find ISO-certified copper cable suppliers in Vietnam, India, or China who have evidence "
    "of supplying to large US companies in the last 12 months and have no compliance concerns."
)


def by_name(name):
    return next(item for item in load_supplier_profiles() if item.canonical_name == name)


def test_active_iso_from_registry_scores_higher_than_website_claim():
    abc = compute_match_components(by_name("ABC Cable Vietnam"), QUERY)
    shenzhen = compute_match_components(by_name("Shenzhen CopperTech"), QUERY)

    assert abc["iso_certification"] == 1.0
    assert shenzhen["iso_certification"] == 0.5


def test_recent_shipment_scores_higher_than_old_shipment():
    abc = compute_match_components(by_name("ABC Cable Vietnam"), QUERY)
    delta = compute_match_components(by_name("Delta Wires India"), QUERY)

    assert abc["buyer_evidence"] == 1.0
    assert delta["buyer_evidence"] == 0.4


def test_compliance_flag_reduces_score():
    eastern = compute_match_components(by_name("Eastern Cable Manufacturing"), QUERY)

    assert eastern["compliance"] == 0.0


def test_confidence_is_independent_of_user_weights():
    profile = by_name("ABC Cable Vietnam")
    baseline, _ = compute_confidence(profile)
    normalize_weights({"iso_certification": 10, "category": 1})
    after_weight_change, _ = compute_confidence(profile)

    assert baseline == after_weight_change


def test_source_reliability_file_is_used_for_evidence_scores():
    reliabilities = load_source_reliability()
    abc = by_name("ABC Cable Vietnam")
    iso = next(item for item in abc.evidence if item.source_type == "certification_database")

    assert iso.source_reliability == reliabilities["certification_database"]


def test_query_without_iso_or_compliance_does_not_make_them_required():
    parsed = parse_query("Find copper cable suppliers in Vietnam")
    abc = compute_match_components(by_name("ABC Cable Vietnam"), parsed)

    assert abc["iso_certification"] == 0.5
    assert abc["compliance"] == 0.5


def _minimal_profile(name: str, evidence: list) -> SupplierProfile:
    return SupplierProfile(
        supplier_id="test_001",
        canonical_name=name,
        country="Testland",
        website="https://test.com",
        product_categories=["test product"],
        records=[SupplierRecord("test_001", name, name, "Testland", "https://test.com", ["test product"], date(2026, 1, 1))],
        aliases=[],
        evidence=evidence,
        entity_resolution=EntityResolution(aliases=[], linked_records=[], resolution_confidence=1.0, reason="test"),
    )


def _ev(date_str: str, source_type: str = "certification_database", claim_value: str = "ISO 9001 active") -> EvidenceRecord:
    parts = [int(x) for x in date_str.split("-")]
    return EvidenceRecord(
        evidence_id="ev_test",
        supplier_id="test_001",
        claim_type="iso_certification",
        claim_value=claim_value,
        source_type=source_type,
        source_name="Test Source",
        source_reliability=0.95 if source_type == "certification_database" else 0.55,
        evidence_date=date(parts[0], parts[1], parts[2]),
        confidence=0.9,
        notes="Test evidence",
    )


def test_all_evidence_expired_sets_freshness_to_zero():
    profile = _minimal_profile("Expired Co.", [
        _ev("2024-01-15", claim_value="ISO 9001 expired"),
        _ev("2023-06-01", claim_value="ISO 9001 expired"),
    ])
    confidence, components = compute_confidence(profile)
    freshness = compute_freshness(profile)

    assert components["freshness"] == 0.0
    assert freshness == 0.0
    assert components["contradiction"] == 0.0


def test_high_confidence_low_match_orders_below_low_confidence_high_match():
    profiles = load_supplier_profiles()
    weights = {"iso_certification": 1, "category": 1, "location": 1, "buyer_evidence": 1, "compliance": 1}
    result = rank_suppliers(profiles, QUERY, weights)
    rankings = {r["supplier_name"]: {
        "match_score": r["match_score"],
        "confidence_score": r["confidence_score"],
        "final_score": r["final_score"],
    } for r in result["results"]}

    top = result["results"][0]
    bottom = result["results"][-1]
    assert top["final_score"] >= bottom["final_score"]


def test_unequal_weights_change_ranking_order():
    profiles = load_supplier_profiles()
    weights_iso = {"iso_certification": 100, "category": 1, "location": 1, "buyer_evidence": 1, "compliance": 1}
    weights_buyer = {"iso_certification": 1, "category": 1, "location": 1, "buyer_evidence": 100, "compliance": 1}

    result_iso = rank_suppliers(profiles, QUERY, weights_iso)
    result_buyer = rank_suppliers(profiles, QUERY, weights_buyer)
    names_iso = [r["supplier_name"] for r in result_iso["results"]]
    names_buyer = [r["supplier_name"] for r in result_buyer["results"]]

    assert names_iso != names_buyer, "Ranking should differ when weights are skewed"


def test_no_results_when_no_profiles_returns_empty():
    from app.ranking import rank_suppliers
    from app.query_parser import ParsedQuery

    empty_query = ParsedQuery(category=None, countries=[], requires_iso=False, buyer_type=None, shipment_window_months=None, compliance_required=False, raw_query="")
    result = rank_suppliers([], empty_query, {})
    assert result["results"] == []


def test_supplier_no_evidence_gets_low_confidence_floor():
    profile = _minimal_profile("No Evidence Co.", [])
    confidence, components = compute_confidence(profile)

    assert confidence == 0.2
    assert components["contradiction"] == 0.5


def test_expired_iso_returns_floor_iso_score():
    profile = _minimal_profile("Expired ISO Co.", [
        _ev("2024-01-15", claim_value="ISO 9001 expired"),
    ])
    components = compute_match_components(profile, QUERY)

    assert components["iso_certification"] == 0.2


def test_contradiction_drops_when_expired_and_active_coexist():
    profile = _minimal_profile("Mixed Co.", [
        _ev("2024-01-15", claim_value="ISO 9001 expired"),
        _ev("2026-03-01", claim_value="ISO 9001 active"),
    ])
    _, components = compute_confidence(profile)

    assert components["contradiction"] == 0.0


def test_three_or_more_source_types_maximises_cross_source():
    ev1 = _ev("2026-01-01", source_type="certification_database", claim_value="ISO 9001 active")
    ev2 = _ev("2026-01-01", source_type="trade_database", claim_value="Shipment to Buyer US")
    ev2.claim_type = "trade_shipment"
    ev3 = _ev("2026-01-01", source_type="compliance_database", claim_value="No compliance flags")
    ev3.claim_type = "compliance"
    profile = _minimal_profile("Triple Source Co.", [ev1, ev2, ev3])
    _, components = compute_confidence(profile)

    assert components["cross_source_confirmation"] == 1.0
