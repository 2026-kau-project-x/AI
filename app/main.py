"""AI 서비스 진입점. BE 가 내부망으로만 호출하는 Stateless 서비스 (DB 없음, 포트 8001)."""

from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="Project X AI", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")
