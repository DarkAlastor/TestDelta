from fastapi import FastAPI
from loguru import logger

from src.parcel_service.api.routers.v1 import routers_v1


def register_routers(app: FastAPI, api_ver:str) -> None:
    logger.info("Reg routers")

    if "v1" in api_ver:

        for router in routers_v1:
            app.include_router(router, prefix="/v1")
            logger.info("Include debug routers")
