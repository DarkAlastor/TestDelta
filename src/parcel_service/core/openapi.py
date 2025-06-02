from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


class OpenAPIGenerator:
    """
    Генератор кастомной OpenAPI-схемы c расширенными возможностями:

    - Автоматическая разметка маршрутов тегами на основе префиксов.
    - Добавление глобальных заголовков.
    - Возможность сокрытия внутренних (админских) маршрутов из документации.

    Используется для настройки читаемой и безопасной Swagger-документации,
    особенно в окружениях c различными уровнями доступа.
    """

    def __init__(
        self,
        app: FastAPI,
        *,
        title: str = "My API",
        version: str = "1.0.0",
        description: str = "",
    ):
        self.app = app
        self.title = title
        self.version = version
        self.description = description

        # Теги по смыслу
        self.public_tags = {"Parcel"}
        self.monitoring_tags = {"Monitoring"}
        self.debug = {"Debug"}
        self.hidden_tags = {"Monitoring", "Debug"}

        # Префикс пути → тег
        self.prefix_tag_map: Dict[str, str] = {
            "/v1/admin": "Admin",
            "/monitoring": "Monitoring",
            "/v1/public": "Public",
        }

    def generate(self, include_internal: bool = False) -> Dict[str, Any]:
        """
        Генерирует OpenAPI-схему c учётом модификаций.

        :param include_internal: Если False — скрывает маршруты c тегом "Admin"
        :return: Полная OpenAPI-схема (dict)
        """
        schema = get_openapi(
            title=self.title,
            version=self.version,
            description=self.description,
            routes=self.app.routes,
        )
        self._mark_routes(schema)
        self._add_global_headers(schema)

        if not include_internal:
            self._remove_internal_routes(schema)

        return schema

    def _mark_routes(self, schema: dict) -> None:
        """
        Назначает тег маршрутам по префиксу пути.
        """
        for path, methods in schema.get("paths", {}).items():
            tag = self._get_tag_for_path(path)
            if tag:
                for method_data in methods.values():
                    method_data.setdefault("tags", []).append(tag)

    def _get_tag_for_path(self, path: str) -> Optional[str]:
        """
        Возвращает тег по заданному префиксу маршрута.

        :param path: путь из OpenAPI
        :return: соответствующий тег или None
        """
        for prefix, tag in self.prefix_tag_map.items():
            if path.startswith(prefix):
                return tag
        return None

    def _add_global_headers(self, schema: dict) -> None:
        """
        Добавляет глобальные заголовки и security-схему для защищённых ручек.
        """
        for path_item in schema.get("paths", {}).values():
            for method in path_item.values():
                method.setdefault("parameters", [])
                tags = method.get("tags", [])

                if any(tag in self.monitoring_tags for tag in tags):
                    self._add_header_param(method, "X-Client-Id", required=True, desc="Client ID (required)")


    def _add_header_param(self, method: dict, name: str, required: bool, desc: str) -> None:
        """
        Добавляет заголовок в OpenAPI, если он ещё не присутствует.
        """
        if not any(p["name"] == name for p in method["parameters"]):
            method["parameters"].append({
                "name": name,
                "in": "header",
                "required": required,
                "schema": {"type": "string"},
                "description": desc,
            })

    def _remove_internal_routes(self, schema: dict) -> None:
        """
        Удаляет маршруты, содержащие хотя бы один тег из self.hidden_tags.
        """
        paths = schema.get("paths", {})
        for path, methods in list(paths.items()):
            methods_to_keep = {
                method: data
                for method, data in methods.items()
                if not any(tag in self.hidden_tags for tag in data.get("tags", []))
            }
            if methods_to_keep:
                schema["paths"][path] = methods_to_keep
            else:
                del schema["paths"][path]
