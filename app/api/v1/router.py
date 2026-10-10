from fastapi import APIRouter

from app.api.v1.endpoints import health, optimize, predict

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(predict.router)
api_router.include_router(optimize.router)
