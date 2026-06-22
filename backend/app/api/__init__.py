from fastapi import APIRouter

from app.api import admin, auth, billing, documents, reports


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(reports.router)
api_router.include_router(billing.router)
api_router.include_router(admin.router)
