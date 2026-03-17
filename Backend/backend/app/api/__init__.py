from fastapi import APIRouter
from app.api.routes import auth, submissions, chat, reports

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(submissions.router)
api_router.include_router(chat.router)
api_router.include_router(reports.router)
