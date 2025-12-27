# backend/app/api/routes/scores.py
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.db import db_session
from app.schemas.scores import SubmitSelfRequest, SubmitPeerRequest, OkResponse

from app.schemas.scores import SubmitTeacherRequest  # Step 8-3

import json
import sqlite3
from pathlib import Path        #Step10-1

from app.services.users_csv import get_students
from app.services.peer_assignments_csv import get_targets_for_rater

def students_set_from_users_csv() -> set[str]:
    return set(get_students())

router = APIRouter(prefix="/api/scores", tags=["scores"])

#ROSTER_PATH = Path(__file__).resolve().parents[2] / "data" / "roster.json"

#def load_students() -> set[str]:
#    data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
#    return set(data.get("students", []))

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/self", response_model=OkResponse)
def submit_self(payload: SubmitSelfRequest, user=Depends(get_current_user)):
    if user["role"] != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail={"ok": False, "error": "FORBIDDEN"})

    s = payload.scores
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO scores_self (user_id, created_at, hp, atk, def, spa, spd, spe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user["user_id"], now_iso(), s.hp, s.atk, s.def_, s.spa, s.spd, s.spe),
        )
    return OkResponse()


@router.post("/peer", response_model=OkResponse)
def submit_peer(payload: SubmitPeerRequest, user=Depends(get_current_user)):
    if user["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"ok": False, "error": "FORBIDDEN"}
        )

    rater = user["user_id"]
    target = payload.target_user_id.strip()

    # 2) 不能評自己
    if target == rater:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"ok": False, "error": "CANNOT_RATE_SELF"}
        )

    students_set = students_set_from_users_csv()

    if rater not in students_set:
        raise HTTPException(status_code=400, detail={"ok": False, "error": "RATER_NOT_IN_USERS_STUDENTS"})
    
    if target not in students_set:
        raise HTTPException(status_code=400, detail={"ok": False, "error": "TARGET_NOT_IN_USERS_STUDENTS"})
    
    if target == rater:
        raise HTTPException(status_code=400, detail={"ok": False, "error": "CANNOT_RATE_SELF"})
    
    allowed = get_targets_for_rater(rater)  # ✅ 改用 peer_assignments.csv
    if target not in allowed:
        raise HTTPException(status_code=403, detail={"ok": False, "error": "TARGET_NOT_ASSIGNED"})


    s = payload.scores

    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO scores_peer (rater_user_id, target_user_id, created_at, hp, atk, def, spa, spd, spe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rater_user_id, target_user_id) DO UPDATE SET
                created_at = excluded.created_at,
                hp = excluded.hp,
                atk = excluded.atk,
                def = excluded.def,
                spa = excluded.spa,
                spd = excluded.spd,
                spe = excluded.spe
            """,
            (rater, target, now_iso(),
             s.hp, s.atk, s.def_, s.spa, s.spd, s.spe),
        )

    return OkResponse()




@router.post("/teacher", response_model=OkResponse)
def submit_teacher(payload: SubmitTeacherRequest, user=Depends(get_current_user)):
    if user["role"] != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail={"ok": False, "error": "FORBIDDEN"})

    # ✅ Step 10：限制 target_user_id 必須在 roster 內
    try:
        students = students_set_from_users_csv()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={"ok": False, "error": "USERS_CSV_NOT_FOUND"})
    except Exception:
        raise HTTPException(status_code=500, detail={"ok": False, "error": "USERS_CSV_READ_ERROR"})

    target = payload.target_user_id.strip()
    if target not in students:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "error": "TARGET_NOT_IN_USERS_STUDENTS"},
        )

    s = payload.scores

    try:

        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO scores_teacher (teacher_user_id, target_user_id, created_at, hp, atk, def, spa, spd, spe)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(teacher_user_id, target_user_id) DO UPDATE SET
                    created_at = excluded.created_at,
                    hp = excluded.hp,
                    atk = excluded.atk,
                    def = excluded.def,
                    spa = excluded.spa,
                    spd = excluded.spd,
                    spe = excluded.spe
                """,
                (user["user_id"], target, now_iso(),
                 s.hp, s.atk, s.def_, s.spa, s.spd, s.spe),
            )

#        with db_session() as conn:
#            conn.execute(
#                """
#                INSERT INTO scores_teacher (teacher_user_id, target_user_id, created_at, hp, atk, def, spa, spd, spe)
#                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#                """,
#                (user["user_id"], target, now_iso(),
#                 s.hp, s.atk, s.def_, s.spa, s.spd, s.spe),
#            )
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500,
            detail={"ok": False, "error": "DB_ERROR", "message": str(e)}
        )

    return OkResponse()

