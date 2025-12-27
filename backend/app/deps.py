# backend/app/deps.py
from __future__ import annotations

from fastapi import Header, HTTPException, status

# 先沿用 Step2 的 demo token：demo.<role>.<user_id>
def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"ok": False, "error": "MISSING_TOKEN"})

    try:
        token_type, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"ok": False, "error": "BAD_AUTH_HEADER"})

    if token_type.lower() not in ("bearer", "demo"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"ok": False, "error": "BAD_TOKEN_TYPE"})

    if not token.startswith("demo."):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"ok": False, "error": "INVALID_TOKEN"})

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"ok": False, "error": "INVALID_TOKEN"})

    _, role, user_id = parts
    return {"role": role, "user_id": user_id}
