# backend/app/schemas/scores.py
from pydantic import BaseModel, Field


class Scores(BaseModel):
    # 六指標，統一用英文欄位存 DB（畫面仍顯示中文）
    hp: int = Field(..., ge=1, le=10)
    atk: int = Field(..., ge=1, le=10)
    def_: int = Field(..., ge=1, le=10, alias="def")
    spa: int = Field(..., ge=1, le=10)
    spd: int = Field(..., ge=1, le=10)
    spe: int = Field(..., ge=1, le=10)

    class Config:
        populate_by_name = True


class SubmitSelfRequest(BaseModel):
    scores: Scores


class SubmitPeerRequest(BaseModel):
    target_user_id: str
    scores: Scores


class OkResponse(BaseModel):
    ok: bool = True


class SubmitTeacherRequest(BaseModel):
    target_user_id: str
    scores: Scores