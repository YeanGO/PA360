from enum import Enum
from pydantic import BaseModel, Field


class Role(str, Enum):
    teacher = "teacher"
    student = "student"
    master = "master"


class LoginRequest(BaseModel):
    role: Role = Field(..., description="登入角色：teacher/student/master")
    user_id: str = Field(..., min_length=1, description="帳號，例如 T01 / S01 / admin")
    password: str = Field(..., min_length=1, description="密碼")


class LoginResponse(BaseModel):
    ok: bool = True
    role: Role
    user_id: str
    display_name: str | None = None
    next_path: str = Field(..., description="前端登入成功後導向的路徑")
    access_token: str = Field(..., description="示範用 token（之後可換 JWT）")
    token_type: str = "bearer"
