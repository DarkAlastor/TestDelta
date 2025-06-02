from fastapi import APIRouter

from .health import router as routers_healths
from .metric import router as routers_metrics

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

router.include_router(routers_healths)
router.include_router(routers_metrics)
