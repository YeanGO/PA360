# backend/app/api/routes/master.py
from __future__ import annotations

from app.services.users_csv import get_students

import csv
import math
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.db import db_session

POKE_PATH = Path(__file__).resolve().parents[2] / "data" / "poke.csv"
DEFAULT_TOP_K = 3
DEFAULT_METHOD = "euclidean"  # or "manhattan"

# 檔案常數區加一個門檻
MIN_PEER_RECEIVED_FOR_CALC = 1

router = APIRouter(prefix="/api/master", tags=["master"])

W_TEACHER = 0.40
W_SELF = 0.20
W_PEER = 0.40

METRICS = ["hp", "atk", "def", "spa", "spd", "spe"]


def row_to_scores(row) -> dict:
    return {m: float(row[m]) for m in METRICS}


def weighted_scores(teacher: dict, self_: dict, peer: dict) -> dict:
    return {
        m: round(W_TEACHER * teacher[m] + W_SELF * self_[m] + W_PEER * peer[m], 2)
        for m in METRICS
    }


@router.get("/summary", summary="Master 加權總分（老師40/自評20/同儕40）")
def summary(user=Depends(get_current_user)):
    if user["role"] != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"ok": False, "error": "FORBIDDEN"},
        )

    students = get_students()

    with db_session() as conn:
        # 1) 自評：取每位學生最新一筆（max id）
        self_rows = conn.execute("""
            SELECT s.user_id, s.hp, s.atk, s.def, s.spa, s.spd, s.spe
            FROM scores_self s
            JOIN (
                SELECT user_id, MAX(id) AS max_id
                FROM scores_self
                GROUP BY user_id
            ) last ON last.user_id = s.user_id AND last.max_id = s.id
        """).fetchall()
        self_map = {r["user_id"]: row_to_scores(r) for r in self_rows}

        # 2) 老師評分：同一學生可能多位老師 → 取平均
        teacher_rows = conn.execute("""
            SELECT target_user_id AS user_id,
                   AVG(hp) AS hp, AVG(atk) AS atk, AVG(def) AS def,
                   AVG(spa) AS spa, AVG(spd) AS spd, AVG(spe) AS spe
            FROM scores_teacher
            GROUP BY target_user_id
        """).fetchall()
        teacher_map = {r["user_id"]: row_to_scores(r) for r in teacher_rows}

        # 3) 同儕收到：取平均
        peer_rows = conn.execute("""
            SELECT target_user_id AS user_id,
                   AVG(hp) AS hp, AVG(atk) AS atk, AVG(def) AS def,
                   AVG(spa) AS spa, AVG(spd) AS spd, AVG(spe) AS spe
            FROM scores_peer
            GROUP BY target_user_id
        """).fetchall()
        peer_map = {r["user_id"]: row_to_scores(r) for r in peer_rows}

        # 在 summary() 裡新增「同儕收到份數」查詢
        peer_cnt_rows = conn.execute("""
            SELECT target_user_id AS user_id, COUNT(*) AS cnt
            FROM scores_peer
            GROUP BY target_user_id
        """).fetchall()
        peer_cnt_map = {r["user_id"]: int(r["cnt"]) for r in peer_cnt_rows}

    detail = []
    for sid in students:
        has_teacher = sid in teacher_map
        has_self = sid in self_map
        peer_received_count = peer_cnt_map.get(sid, 0)

        has_peer = peer_received_count >= MIN_PEER_RECEIVED_FOR_CALC
        complete = has_teacher and has_self and has_peer

        item = {
            "user_id": sid,
            "has_teacher": has_teacher,
            "has_self": has_self,
            "has_peer": has_peer,
            "peer_received_count": peer_received_count,
            "complete": complete,
            "teacher_avg": teacher_map.get(sid),
            "self_latest": self_map.get(sid),
            "peer_avg": peer_map.get(sid),
            "weighted": None,
            "weighted_mean": None,
        }

        if complete:
            w = weighted_scores(teacher_map[sid], self_map[sid], peer_map[sid])
            item["weighted"] = w
            item["weighted_mean"] = round(sum(w[m] for m in METRICS) / len(METRICS), 2)

        detail.append(item)

    done = sum(1 for x in detail if x["complete"])
    return {
        "ok": True,
        "weights": {"teacher": W_TEACHER, "self": W_SELF, "peer": W_PEER},
        "class_size": len(students),
        "complete_count": done,
        "detail": detail,
    }


def load_pokemon() -> list[dict]:
    if not POKE_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail={"ok": False, "error": "POKE_CSV_NOT_FOUND", "path": str(POKE_PATH)},
        )

    pokes: list[dict] = []
    with POKE_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"poke_num", "poke_name", *METRICS}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise HTTPException(
                status_code=500,
                detail={"ok": False, "error": "POKE_CSV_BAD_COLUMNS", "columns": reader.fieldnames},
            )

        for row in reader:
            try:
                poke_num = int(row["poke_num"])
                poke_name = str(row["poke_name"])
                stats = {m: float(row[m]) for m in METRICS}
            except Exception:
                continue

            pokes.append({
                "poke_num": poke_num,
                "poke_name": poke_name,
                "stats": stats,
            })

    return pokes


def dist(a: dict, b: dict, method: str) -> float:
    if method == "manhattan":
        return sum(abs(a[m] - b[m]) for m in METRICS)
    # default euclidean
    return math.sqrt(sum((a[m] - b[m]) ** 2 for m in METRICS))


def get_weighted_map() -> dict[str, dict]:
    """回傳：{student_id: weighted_scores_dict}，只包含 complete 的學生"""
    students = get_students()

    with db_session() as conn:
        self_rows = conn.execute("""
            SELECT s.user_id, s.hp, s.atk, s.def, s.spa, s.spd, s.spe
            FROM scores_self s
            JOIN (
                SELECT user_id, MAX(id) AS max_id
                FROM scores_self
                GROUP BY user_id
            ) last ON last.user_id = s.user_id AND last.max_id = s.id
        """).fetchall()
        self_map = {r["user_id"]: row_to_scores(r) for r in self_rows}

        teacher_rows = conn.execute("""
            SELECT target_user_id AS user_id,
                   AVG(hp) AS hp, AVG(atk) AS atk, AVG(def) AS def,
                   AVG(spa) AS spa, AVG(spd) AS spd, AVG(spe) AS spe
            FROM scores_teacher
            GROUP BY target_user_id
        """).fetchall()
        teacher_map = {r["user_id"]: row_to_scores(r) for r in teacher_rows}

        peer_rows = conn.execute("""
            SELECT target_user_id AS user_id,
                   AVG(hp) AS hp, AVG(atk) AS atk, AVG(def) AS def,
                   AVG(spa) AS spa, AVG(spd) AS spd, AVG(spe) AS spe
            FROM scores_peer
            GROUP BY target_user_id
        """).fetchall()
        peer_map = {r["user_id"]: row_to_scores(r) for r in peer_rows}

    weighted_map: dict[str, dict] = {}
    for sid in students:
        if sid in teacher_map and sid in self_map and sid in peer_map:
            weighted_map[sid] = weighted_scores(teacher_map[sid], self_map[sid], peer_map[sid])
    return weighted_map


def to_pokemon_com_slug(name: str) -> str:
    """
    把 poke_name 轉成 pokemon.com 的 pokedex slug（多數英文名可用）
    例: "Pikachu" -> "pikachu"
        "Mr. Mime" -> "mr-mime"（點號會被移除、空白變連字號）
        "Farfetch'd" -> "farfetchd"（撇號移除）
    """
    s = (name or "").strip().lower()
    s = s.replace("♀", "-f").replace("♂", "-m")  # 少見但安全處理
    s = re.sub(r"\s+", "-", s)                   # 空白 -> -
    s = re.sub(r"[^a-z0-9-]", "", s)             # 移除其他符號（' . 等）
    s = re.sub(r"-{2,}", "-", s).strip("-")      # 多個 - 合併、去頭尾
    return s


@router.get("/match", summary="Master：Top-K 相似寶可夢（用加權六指標）")
def match(
    student_id: str,
    top_k: int = DEFAULT_TOP_K,
    method: str = DEFAULT_METHOD,
    user=Depends(get_current_user),
):
    if user["role"] != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"ok": False, "error": "FORBIDDEN"}
        )

    method = (method or "euclidean").lower().strip()
    if method not in ("euclidean", "manhattan"):
        raise HTTPException(status_code=400, detail={"ok": False, "error": "BAD_METHOD"})

    top_k = max(1, min(int(top_k), 20))  # 防呆：最多 20

    weighted_map = get_weighted_map()
    sid = student_id.strip()

    if sid not in weighted_map:
        # 代表資料不齊（老師/自評/同儕缺一）
        return {
            "ok": True,
            "student_id": sid,
            "complete": False,
            "reason": "NEED_TEACHER_SELF_PEER",
            "method": method,
            "top_k": top_k,
            "weighted": None,
            "results": [],
        }

    base = weighted_map[sid]
    pokes = load_pokemon()

    scored = []
    for p in pokes:
        d = dist(base, p["stats"], method)
        slug = to_pokemon_com_slug(p["poke_name"])

        scored.append({
            "poke_num": p["poke_num"],
            "poke_name": p["poke_name"],
            "distance": round(float(d), 4),
            "stats": p["stats"],
            # 台灣官方圖鑑：poke_num 補 4 碼
            "official_url": f"https://tw.portal-pokemon.com/play/pokedex/{p['poke_num']:04d}",
        })

    # 距離小的優先；平手取 poke_num 小的（符合規格書）
    scored.sort(key=lambda x: (x["distance"], x["poke_num"]))

    return {
        "ok": True,
        "student_id": sid,
        "complete": True,
        "method": method,
        "top_k": top_k,
        "weighted": base,
        "results": scored[:top_k],
    }
