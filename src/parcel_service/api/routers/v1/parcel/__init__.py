from fastapi import APIRouter

from .create_parcel import router as routers_create_parcel
from .get_parcel import router as routers_get_parcel
from .bind_company import router as router_bind_company

router = APIRouter(prefix="/parcels", tags=["Parcel"])

router.include_router(routers_get_parcel)
router.include_router(routers_create_parcel)
router.include_router(router_bind_company)
