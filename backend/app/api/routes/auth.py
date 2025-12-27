import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, LoginResponse, Role

router = APIRouter(prefix="/api/auth", tags=["auth"])

#  Step 2 先用「假資料」：下一步再換成讀 CSV 或 DB
#_DEMO_USERS = {
#    ("teacher", "T01"): {"password": "1234", "display_name": "Teacher-01"},
#    ("student", "S01"): {"password": "1234", "display_name": "Student-01"},
#    ("student", "S02"): {"password": "1234", "display_name": "Student-01"},
#    ("student", "S03"): {"password": "1234", "display_name": "Student-01"},
#    ("master",  "admin"): {"password": "1234", "display_name": "Pokemon Master"},
#}

# users.csv 路徑：backend/app/data/users.csv
USERS_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "users.csv"

def load_users_from_csv() -> dict[tuple[str, str], dict]:
    """
    回傳格式：
    {
      ("teacher","T01"): {"password":"1234","display_name":"Teacher-01"},
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

# ✅ 取代原本 _DEMO_USERS：啟動時載入一次（開發期最簡單）
_USERS = load_users_from_csv()



_ROLE_TO_NEXT = {
    Role.teacher: "/teacher/index.html",
    Role.student: "/student/index.html",
    Role.master:  "/master/index.html",
}


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="登入（回傳角色、導頁路徑、token）",
)
def login(payload: LoginRequest) -> LoginResponse:
    key = (payload.role.value, payload.user_id)
    #user = _DEMO_USERS.get(key)
    user = _USERS.get(key)

    if not user or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"ok": False, "error": "INVALID_CREDENTIALS"},
        )

    # 先用簡單 token：之後可改 JWT + 過期時間
    token = f"demo.{payload.role.value}.{payload.user_id}"

    return LoginResponse(
        role=payload.role,
        user_id=payload.user_id,
        display_name=user.get("display_name"),
        next_path=_ROLE_TO_NEXT[payload.role],
        access_token=token,
    )

#=============================Step4-2=============================

from fastapi import Header

@router.get("/me", summary="檢查目前登入者（驗證 token）")
def me(authorization: str | None = Header(default=None)):
    """
    前端會帶 Authorization: bearer <token>
    這支 API 用來驗證 token 是否有效，並回傳使用者基本資訊。
    """
    if not authorization:
        raise HTTPException(status_code=401, detail={"ok": False, "error": "MISSING_TOKEN"})

    try:
        token_type, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail={"ok": False, "error": "BAD_AUTH_HEADER"})

    # Step 2 產生的 demo token：demo.<role>.<user_id>
    if not token.startswith("demo."):
        raise HTTPException(status_code=401, detail={"ok": False, "error": "INVALID_TOKEN"})

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail={"ok": False, "error": "INVALID_TOKEN"})

    _, role, user_id = parts

    # 驗證是否在 demo 使用者清單中（避免亂造 token），修改 login 驗證：改用 _USERS 
    #user = _DEMO_USERS.get((role, user_id))
    user = _USERS.get((role, user_id))
    if not user:
        raise HTTPException(status_code=401, detail={"ok": False, "error": "INVALID_TOKEN"})

    return {
        "ok": True,
        "role": role,
        "user_id": user_id,
        "display_name": user.get("display_name")
    }

