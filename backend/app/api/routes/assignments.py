# backend/app/api/routes/assignments.py
from __future__ import annotations
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import get_current_user
from app.services.peer_assignments_csv import get_targets_for_rater

router = APIRouter(prefix="/api/assignments", tags=["assignments"])

# ROSTER_PATH = Path(__file__).resolve().parents[2] / "data" / "roster.json"


# def load_students() -> list[str]:
#     data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
#     return list(data.get("students", []))

from app.services.peer_assignments_csv import get_targets_for_rater

@router.get("/peers")
def peers(user=Depends(get_current_user)):
    if user["role"] != "student":
        raise HTTPException(status_code=403, detail={"ok": False, "error": "FORBIDDEN"})

    targets = get_targets_for_rater(user["user_id"])
    return targets



# @router.get("/peers")
# def get_assigned_peers(user=Depends(get_current_user)):
#     if user["role"] != "student":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                             detail={"ok": False, "error": "FORBIDDEN"})

#     students = load_students()
#     me = user["user_id"]
#     if me not in students:
#         raise HTTPException(status_code=400, detail={"ok": False, "error": "USER_NOT_IN_ROSTER"})

#     i = students.index(me)
#     # 每人 2 位（可擴充：改 range(1, N+1)）
#     assigned = [students[(i + 1) % len(students)], students[(i + 2) % len(students)]]
#     return {"ok": True, "user_id": me, "assigned_peers": assigned}
