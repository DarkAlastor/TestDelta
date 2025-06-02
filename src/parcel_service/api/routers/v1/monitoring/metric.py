from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import REGISTRY, generate_latest

router = APIRouter()

@router.get(path="/metrics", summary="Endpoint для prometheus")
async def metrics() -> Response:
    """
    Возвращает метрики Prometheus в формате `text/plain`.

    Используется системой мониторинга Prometheus для сбора метрик приложения.

    :return: HTTP-ответ с метриками Prometheus.
    :rtype: Response
    """
    return Response(generate_latest(REGISTRY), media_type="text/plain; version=0.0.4; charset=utf-8", status_code=200)