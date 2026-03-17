from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import auth, submissions, agent, reports, lender, history, settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="CreditAI API",
    description="AI-powered credit scoring for the unbanked",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = settings.API_PREFIX

app.include_router(auth.router,        prefix=PREFIX)
app.include_router(submissions.router, prefix=PREFIX)
app.include_router(agent.router,       prefix=PREFIX)
app.include_router(reports.router,     prefix=PREFIX)
app.include_router(lender.router,      prefix=PREFIX)
app.include_router(history.router,     prefix=PREFIX)
app.include_router(settings_router.router, prefix=PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
