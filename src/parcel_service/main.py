from fastapi import FastAPI

from src.parcel_service.api import register_routers
from src.parcel_service.core.config import Settings
from src.parcel_service.core.container import register_container
from src.parcel_service.core.exceptions import register_exceptions


def create_app() -> FastAPI:
    """
    Создаёт и настраивает экземпляр FastAPI-приложения.

    Конфигурация включает:
    - Загрузку настроек из класса `Settings`
    - Регистрацию контейнера зависимостей (DI)
    - Регистрацию глобальных обработчиков исключений
    - Регистрацию маршрутов по версии API

    :return: Настроенное FastAPI-приложение.
    :rtype: FastAPI
    """

    settings = Settings.load()

    app = FastAPI(
        title=settings.meta.title_app,
        version=settings.meta.version_app,
        description=settings.meta.description_app,
        docs_url=settings.meta.docs_url_app,
        redoc_url=settings.meta.redoc_url_app,
        openapi_url=settings.meta.openapi_url_app,
        debug=settings.app.debug,
    )

    register_container(app=app, settings=settings)
    register_exceptions(app=app)
    register_routers(app=app, api_ver=settings.app.api_version)
    return app

app = create_app()

