from app.data_loader import load_supplier_profiles
from app.query_parser import parse_query
from app.ranking import rank_suppliers
from app.scoring import normalize_weights


QUERY = parse_query(
    "Find ISO-certified copper cable suppliers in Vietnam, India, or China who have evidence "
    "of supplying to large US companies in the last 12 months and have no compliance concerns."
)


def test_strong_verified_supplier_ranks_first_with_default_weights():
    ranked = rank_suppliers(load_supplier_profiles(), QUERY, {})

    assert ranked["results"][0]["supplier_name"] == "ABC Cable Vietnam"
    assert ranked["results"][0]["supplier_id"] == "sup_001"


def test_missing_iso_supplier_drops_when_iso_weight_is_increased():
    default = rank_suppliers(load_supplier_profiles(), QUERY, {})
    iso_heavy = rank_suppliers(
        load_supplier_profiles(),
        QUERY,
        {
            "category": 0.1,
            "location": 0.05,
            "iso_certification": 0.6,
            "buyer_evidence": 0.1,
            "compliance": 0.15,
        },
    )

    default_rank = {
        item["supplier_name"]: item["rank"]
        for item in default["results"]
    }["Guangzhou Power Cable Group"]
    iso_rank = {
        item["supplier_name"]: item["rank"]
        for item in iso_heavy["results"]
    }["Guangzhou Power Cable Group"]
    assert iso_rank > default_rank


def test_invalid_weight_totals_are_normalized():
    weights = normalize_weights({"category": 5, "location": 5})

    assert round(sum(weights.values()), 6) == 1.0


def test_all_zero_weights_fall_back_to_defaults():
    weights = normalize_weights(
        {
            "category": 0,
            "location": 0,
            "iso_certification": 0,
            "buyer_evidence": 0,
            "compliance": 0,
        }
    )

    assert weights == {
        "category": 0.25,
        "location": 0.15,
        "iso_certification": 0.2,
        "buyer_evidence": 0.25,
        "compliance": 0.15,
    }
