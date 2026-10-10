from fastapi import APIRouter, Depends

from app.schemas.predict import PredictRequest, PredictResponse
from app.services.wait_time import WaitTimeModel, get_wait_time_model

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest, model: WaitTimeModel = Depends(get_wait_time_model)):
    """이동지원차량 대기시간 예측. 상태를 저장하지 않는다(Stateless)."""
    return model.predict(body)
