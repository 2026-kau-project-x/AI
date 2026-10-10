from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    # ECS 헬스체크 대상. 모델 로드 실패 등을 반영하려면 여기서 상태를 확인하도록 확장한다
    return {"status": "ok"}
