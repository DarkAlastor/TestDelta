from fastapi import APIRouter

from .recalculate import router as recalculate_router
from .session_id import router as session_id_router

router = APIRouter(prefix="/debug", tags=["Debug"])
router.include_router(recalculate_router)
router.include_router(session_id_router)
