from app.data_loader import load_source_reliability, load_supplier_profiles
from app.query_parser import parse_query
from app.scoring import compute_confidence, compute_match_components, normalize_weights


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
