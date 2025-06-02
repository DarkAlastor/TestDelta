from fastapi import APIRouter

from .delivery_summary import router as delivery_summary

router = APIRouter(prefix="/analytics", tags=["Analytics"])
router.include_router(delivery_summary)