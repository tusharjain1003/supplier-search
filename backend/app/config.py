from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
DEFAULT_AS_OF_DATE = date(2026, 6, 7)

DEFAULT_WEIGHTS = {
    "category": 0.25,
    "location": 0.15,
    "iso_certification": 0.20,
    "buyer_evidence": 0.25,
    "compliance": 0.15,
}

