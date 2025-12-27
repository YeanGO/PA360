from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes.auth import router as auth_router
from app.api.routes.scores import router as scores_router
from app.api.routes.assignments import router as assignments_router
from app.api.routes.teacher import router as teacher_router
from app.db import init_db

from app.api.routes.master import router as master_router

app = FastAPI(title="Pokemon Ability Evaluation API")

app.include_router(auth_router)
app.include_router(scores_router)
app.include_router(assignments_router)
app.include_router(teacher_router)
app.include_router(master_router)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
