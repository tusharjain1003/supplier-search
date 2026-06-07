from app.query_parser import clarification_questions, parse_query


def test_default_query_extracts_core_criteria():
    parsed = parse_query(
        "Find ISO-certified copper cable suppliers in Vietnam, India, or China "
        "who have evidence of supplying to large US companies in the last 12 months "
        "and have no compliance concerns."
    )

    assert parsed.category == "copper cable"
    assert parsed.countries == ["Vietnam", "India", "China"]
    assert parsed.requires_iso is True
    assert parsed.buyer_type == "large US companies"
    assert parsed.shipment_window_months == 12
    assert parsed.compliance_required is True


def test_ambiguous_query_requests_clarification():
    parsed = parse_query("Find suppliers with good evidence")

    assert "Which product category are you looking for?" in clarification_questions(parsed)
    assert "Which supplier countries should be included?" in clarification_questions(parsed)


def test_query_without_iso_is_not_automatically_ambiguous():
    parsed = parse_query("Find copper cable suppliers in Vietnam")

    assert clarification_questions(parsed) == []
