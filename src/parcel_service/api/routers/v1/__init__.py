from src.parcel_service.api.routers.v1.debug import router as debug_routers
from src.parcel_service.api.routers.v1.monitoring import router as monitoring_routers
from src.parcel_service.api.routers.v1.parcel import router as parcel_routers
from src.parcel_service.api.routers.v1.analytics import router as analytics_router

routers_v1 = [parcel_routers, debug_routers, monitoring_routers, analytics_router]
