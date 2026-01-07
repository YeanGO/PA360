# backend/app/api/routes/teacher.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import get_current_user
from app.db import db_session
from app.services.users_csv import get_students

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

@router.get("/completion", summary="老師查看全班完成度（自評/同儕送出/同儕收到）")
def class_completion(user=Depends(get_current_user)):
    # 只允許 teacher
    if user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"ok": False, "error": "FORBIDDEN"},
        )

    students = get_students()
    n = len(students)

    # 我們的同儕規則：每人要評 2 位
    required_peer_given = 2
    # 在環狀分派中，每位學生理論上也會「被 2 位同學評分」
    required_peer_received = 2

    # 先把所有人狀態初始化
    result = {
        sid: {
            "user_id": sid,
            "self_submitted": False,
            "peer_given_count": 0,
            "peer_received_count": 0,
            "required_peer_given": required_peer_given,
            "required_peer_received": required_peer_received,

            #新增
            "teacher_scored": False,
            "required_teacher": 1,
        }
        for sid in students
    }

    with db_session() as conn:
        # 自評：每人只要有一筆，就算完成（也可改成看 latest）
        rows = conn.execute("""
            SELECT user_id, COUNT(*) AS cnt
            FROM scores_self
            GROUP BY user_id
        """).fetchall()
        for r in rows:
            uid = r["user_id"]
            if uid in result:
                result[uid]["self_submitted"] = (r["cnt"] > 0)

        # 同儕送出：每人送出幾筆
        rows = conn.execute("""
            SELECT rater_user_id AS user_id, COUNT(*) AS cnt
            FROM scores_peer
            GROUP BY rater_user_id
        """).fetchall()
        for r in rows:
            uid = r["user_id"]
            if uid in result:
                result[uid]["peer_given_count"] = int(r["cnt"])

        # 同儕收到：每人被評幾筆
        rows = conn.execute("""
            SELECT target_user_id AS user_id, COUNT(*) AS cnt
            FROM scores_peer
            GROUP BY target_user_id
        """).fetchall()
        for r in rows:
            uid = r["user_id"]
            if uid in result:
                result[uid]["peer_received_count"] = int(r["cnt"])

        # 老師評分：每位學生是否已被老師評過（target_user_id 只要有一筆就算完成）
        rows = conn.execute("""
            SELECT target_user_id AS user_id, COUNT(*) AS cnt
            FROM scores_teacher
            GROUP BY target_user_id
        """).fetchall()
        for r in rows:
            uid = r["user_id"]
            if uid in result:
                result[uid]["teacher_scored"] = (int(r["cnt"]) >= 1)


    # 統計：哪些人沒交
    not_submitted_self = [sid for sid in students if not result[sid]["self_submitted"]]
    not_done_peer_given = [
        sid for sid in students if result[sid]["peer_given_count"] < required_peer_given
    ]
    not_done_teacher = [sid for sid in students if not result[sid]["teacher_scored"]]


    # 全班明細（照 roster 順序）
    detail = []
    for sid in students:
        item = result[sid]
        #item["peer_given_done"] = (item["peer_given_count"] >= required_peer_given)
        #item["peer_received_done"] = (item["peer_received_count"] >= required_peer_received)
        #item["all_done"] = (item["self_submitted"] and item["peer_given_done"])
        item["peer_given_done"] = (item["peer_given_count"] >= required_peer_given)
        item["peer_received_done"] = (item["peer_received_count"] >= required_peer_received)

        # 老師評分是否完成（已在 teacher_scored）
        item["teacher_done"] = item["teacher_scored"]
        
        # all_done：自評 + 同儕送出達標 + 老師評分完成
        item["all_done"] = (item["self_submitted"] and item["peer_given_done"] and item["teacher_done"])

        detail.append(item)

    return {
        "ok": True,
        "class_size": n,
        "required_peer_given": required_peer_given,
        "required_peer_received": required_peer_received,
        "not_submitted_self": not_submitted_self,
        "not_done_peer_given": not_done_peer_given,
        "detail": detail,
        "not_done_teacher": not_done_teacher,
    }


# @router.get("/students", summary="老師取得全班學生名單（roster）")
# def get_students(user=Depends(get_current_user)):
#     if user["role"] != "teacher":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail={"ok": False, "error": "FORBIDDEN"},
#         )
#     students = get_students()
#     return {"ok": True, "students": students}

@router.get("/students")
def list_students_api(user=Depends(get_current_user)):
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail={"ok": False})

    students = get_students()
    return {"ok": True, "students": students}
