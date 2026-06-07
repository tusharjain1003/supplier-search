import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.data_loader import get_supplier_profile, load_supplier_profiles
from app.explanations import evidence_summary
from app.query_parser import parse_query
from app.ranking import rank_suppliers


DEFAULT_QUERY = (
    "Find ISO-certified copper cable suppliers in Vietnam, India, or China who have evidence "
    "of supplying to large US companies in the last 12 months and have no compliance concerns."
)


st.set_page_config(page_title="Supplier Search", layout="wide")
st.title("Supplier Search")

query = st.text_area("Supplier search query", value=DEFAULT_QUERY, height=95)

st.subheader("Preference weights")
columns = st.columns(5)
weights = {
    "category": columns[0].slider("Category", 0, 100, 25),
    "location": columns[1].slider("Location", 0, 100, 15),
    "iso_certification": columns[2].slider("ISO certification", 0, 100, 20),
    "buyer_evidence": columns[3].slider("Buyer evidence", 0, 100, 25),
    "compliance": columns[4].slider("Compliance", 0, 100, 15),
}

parsed = parse_query(query)
ranked = rank_suppliers(load_supplier_profiles(), parsed, {key: value / 100 for key, value in weights.items()})

with st.expander("Parsed criteria", expanded=True):
    st.json(
        {
            "category": parsed.category,
            "countries": parsed.countries,
            "requires_iso": parsed.requires_iso,
            "buyer_type": parsed.buyer_type,
            "shipment_window_months": parsed.shipment_window_months,
            "compliance_required": parsed.compliance_required,
            "normalized_weights": ranked["weights"],
        }
    )

rows = [
    {
        "Rank": result["rank"],
        "Supplier": result["supplier_name"],
        "Country": result["country"],
        "Match": result["match_score"],
        "Confidence": result["confidence_score"],
        "Freshness": result["freshness_score"],
        "Final": result["final_score"],
        "Why ranked": result["explanation"],
    }
    for result in ranked["results"]
]
st.dataframe(rows, use_container_width=True, hide_index=True)

st.subheader("Supplier evidence")
for result in ranked["results"][:8]:
    with st.expander(f"#{result['rank']} {result['supplier_name']} - final score {result['final_score']}"):
        profile = get_supplier_profile(result["supplier_id"])
        st.write(result["explanation"])
        if result["weaknesses"]:
            st.markdown("Weak or missing evidence")
            for weakness in result["weaknesses"]:
                st.write(f"- {weakness}")
        st.markdown("Matched criteria")
        st.json(result["matched_criteria"])
        st.markdown("Confidence breakdown")
        st.json(result["confidence_components"])
        st.markdown("Entity resolution")
        st.json(
            {
                "aliases": profile.aliases,
                "linked_records": profile.entity_resolution.linked_records,
                "resolution_confidence": profile.entity_resolution.resolution_confidence,
                "reason": profile.entity_resolution.reason,
            }
        )
        st.markdown("Evidence records")
        st.dataframe(evidence_summary(profile.evidence, limit=100), use_container_width=True, hide_index=True)
