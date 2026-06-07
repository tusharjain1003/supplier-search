from datetime import date

from app.data_loader import load_supplier_profiles
from app.entity_resolution import find_candidate_matches, name_similarity, normalize_name
from app.models import SupplierRecord


def test_normalize_name_removes_legal_suffixes():
    assert normalize_name("ABC Cable Vietnam Ltd.") == "abc cable vietnam"


def test_abc_aliases_are_linked_to_canonical_profile():
    profile = next(item for item in load_supplier_profiles() if item.canonical_name == "ABC Cable Vietnam")

    assert "ABC Cables VN" in profile.aliases
    assert "ABC Cable Co. Vietnam" in profile.aliases
    assert profile.entity_resolution.resolution_confidence >= 0.9


def test_similar_names_from_different_countries_are_not_identical():
    assert name_similarity("ABC Cable Vietnam Ltd.", "Eastern Cable Manufacturing") < 0.8


def test_candidate_matches_are_reported_but_not_merged():
    profiles = load_supplier_profiles()
    shanghai = next(item for item in profiles if item.canonical_name == "Shanghai Copper Cable Export")

    assert shanghai.entity_resolution.candidate_matches
    assert all(
        candidate["reason"].startswith("Medium name similarity")
        for candidate in shanghai.entity_resolution.candidate_matches
    )


def test_candidate_matching_does_not_cross_country_blocks():
    records = [
        SupplierRecord(
            supplier_id="left",
            supplier_name="Global Copper Cable Ltd.",
            canonical_name="Global Copper Cable India",
            country="India",
            website="https://example.in",
            product_categories=["copper cable"],
            created_at=date(2026, 1, 1),
        ),
        SupplierRecord(
            supplier_id="right",
            supplier_name="Global Copper Cable Ltd.",
            canonical_name="Global Copper Cable Vietnam",
            country="Vietnam",
            website="https://example.vn",
            product_categories=["copper cable"],
            created_at=date(2026, 1, 1),
        ),
    ]

    assert find_candidate_matches(records) == []
