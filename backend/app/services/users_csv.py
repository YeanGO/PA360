from __future__ import annotations

import csv
from pathlib import Path

USERS_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "users.csv"
# ↑ services/ 往上 1 層是 app/，所以 app/data/users.csv

def load_users() -> dict[tuple[str, str], dict]:
    """
    回傳：
    {
      ("student","S01"): {"password":"1234","display_name":"小智"},
      ...
    }
    """
    if not USERS_CSV_PATH.exists():
        raise FileNotFoundError(f"users.csv not found: {USERS_CSV_PATH}")

    users: dict[tuple[str, str], dict] = {}
    with USERS_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"role", "user_id", "password", "display_name"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"users.csv missing columns: need {required}, got {reader.fieldnames}")

        for row in reader:
            role = (row.get("role") or "").strip()
            user_id = (row.get("user_id") or "").strip()
            password = (row.get("password") or "").strip()
            display_name = (row.get("display_name") or "").strip()

            if not role or not user_id:
                continue

            users[(role, user_id)] = {
                "password": password,
                "display_name": display_name or user_id,
            }

    return users


def get_students() -> list[str]:
    """回傳 users.csv 中 role=student 的 user_id，並按 ID 排序。"""
    users = load_users()
    students = [uid for (role, uid) in users.keys() if role == "student"]
    students.sort()
    return students


def get_display_name(role: str, user_id: str) -> str | None:
    users = load_users()
    u = users.get((role, user_id))
    return u.get("display_name") if u else None
