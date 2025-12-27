from __future__ import annotations

import csv
from pathlib import Path

ASSIGNMENTS_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "peer_assignments.csv"
# services/ 往上 1 層是 app/，所以 app/data/peer_assignments.csv

def load_peer_assignments() -> dict[str, list[str]]:
    """
    回傳：
    {
      "S01": ["S02","S03"],
      "S02": ["S03","S04"],
      ...
    }
    """
    if not ASSIGNMENTS_CSV_PATH.exists():
        raise FileNotFoundError(f"peer_assignments.csv not found: {ASSIGNMENTS_CSV_PATH}")

    mapping: dict[str, list[str]] = {}

    with ASSIGNMENTS_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"rater_id", "target_id"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"peer_assignments.csv missing columns: need {required}, got {reader.fieldnames}")

        for row in reader:
            rater = (row.get("rater_id") or "").strip()
            target = (row.get("target_id") or "").strip()
            if not rater or not target:
                continue
            mapping.setdefault(rater, []).append(target)

    return mapping


def get_targets_for_rater(rater_id: str) -> list[str]:
    mapping = load_peer_assignments()
    return mapping.get(rater_id, [])
