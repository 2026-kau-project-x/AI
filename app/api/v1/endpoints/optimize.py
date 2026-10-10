from fastapi import APIRouter, Depends

from app.schemas.optimize import OptimizeRequest, OptimizeResponse
from app.services.rendezvous import RendezvousOptimizer, get_optimizer

router = APIRouter(tags=["optimize"])


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(body: OptimizeRequest, optimizer: RendezvousOptimizer = Depends(get_optimizer)):
    """보행자·목적지·차량 위치로 랑데부(합류) 지점을 고른다. BE 의 HttpAiClient 가 호출한다."""
    return optimizer.optimize(body)
