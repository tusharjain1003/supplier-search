import re
from typing import List, Optional

from .models import ParsedQuery


COUNTRIES = ["Vietnam", "India", "China", "Thailand", "Malaysia", "Mexico", "United States"]
CATEGORY_PATTERNS = {
    "copper cable": [r"copper\s+cables?", r"copper\s+wires?", r"power\s+cables?"],
    "fiber optic cable": [r"fiber\s+optic", r"fibre\s+optic", r"telecom\s+cables?"],
    "aluminum conductor": [r"aluminum\s+conductors?", r"aluminium\s+conductors?"],
}


def _extract_category(query: str) -> Optional[str]:
    lowered = query.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            return category
    return None


def _extract_countries(query: str) -> List[str]:
    lowered = query.lower()
    return [country for country in COUNTRIES if country.lower() in lowered]


def _extract_window(query: str) -> Optional[int]:
    lowered = query.lower()
    month_match = re.search(r"last\s+(\d{1,2})\s+months?", lowered)
    if month_match:
        return int(month_match.group(1))
    year_match = re.search(r"last\s+(\d{1,2})\s+years?", lowered)
    if year_match:
        return int(year_match.group(1)) * 12
    if "recent" in lowered or "current" in lowered:
        return 12
    return None


def parse_query(query: str) -> ParsedQuery:
    lowered = query.lower()
    buyer_type = None
    if "fortune 500" in lowered:
        buyer_type = "Fortune 500 companies"
    elif "large us" in lowered or "major us" in lowered or "us companies" in lowered:
        buyer_type = "large US companies"

    return ParsedQuery(
        category=_extract_category(query),
        countries=_extract_countries(query),
        requires_iso="iso" in lowered,
        buyer_type=buyer_type,
        shipment_window_months=_extract_window(query),
        compliance_required=(
            "no compliance" in lowered
            or "without compliance" in lowered
            or "no sanctions" in lowered
            or "compliance concerns" in lowered
        ),
        raw_query=query,
    )


def clarification_questions(parsed_query: ParsedQuery) -> List[str]:
    questions: List[str] = []
    if not parsed_query.category:
        questions.append("Which product category are you looking for?")
    if not parsed_query.countries:
        questions.append("Which supplier countries should be included?")
    return questions
