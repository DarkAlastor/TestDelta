from typing import Callable, ClassVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.outbox_publisher.core.config import Settings
from src.outbox_publisher.messaging.publisher import RabbitMQPublisher
from src.outbox_publisher.db.engine import create_db_engine, create_session_factory


class AppContainer:
    """
    Контейнер приложения для хранения глобальных зависимостей:
    - фабрики асинхронных сессий SQLAlchemy;
    - экземпляра RabbitMQPublisher.

    Используется как синглтон без необходимости передачи зависимостей явно в каждый компонент.
    """

    _async_session_factory: ClassVar[Optional[Callable[[], AsyncSession]]] = None
    _rabbitmq_publisher: ClassVar[Optional[RabbitMQPublisher]] = None

    @classmethod
    async def init(cls, settings: Settings) -> None:
        """
        Инициализирует глобальные зависимости приложения:
        - подключение к базе данных;
        - соединение с RabbitMQ.

        :param settings: Конфигурация приложения.
        :type settings: Settings
        """
        # Инициализация БД
        db_engine = create_db_engine(db_settings=settings.database, debug=settings.database.echo)
        cls._async_session_factory = create_session_factory(engine=db_engine)

        # Инициализация RabbitMQPublisher
        publisher = RabbitMQPublisher()
        await publisher.connect(settings.rabbitmq)
        cls._rabbitmq_publisher = publisher

    @classmethod
    @property
    def session_factory(cls) -> Callable[[], AsyncSession]:
        """
        Возвращает фабрику для создания асинхронных SQLAlchemy-сессий.

        :raises RuntimeError: если фабрика ещё не инициализирована.
        :return: Callable-фабрика асинхронных сессий.
        :rtype: Callable[[], AsyncSession]
        """
        if cls._async_session_factory is None:
            raise RuntimeError("Session factory is not initialized")
        return cls._async_session_factory

    @classmethod
    @property
    def rabbitmq_publisher(cls) -> RabbitMQPublisher:
        """
        Возвращает инициализированный экземпляр RabbitMQPublisher.

        :raises RuntimeError: если экземпляр ещё не инициализирован.
        :return: Инициализированный RabbitMQPublisher.
        :rtype: RabbitMQPublisher
        """
        if cls._rabbitmq_publisher is None:
            raise RuntimeError("RabbitMQPublisher is not initialized")
        return cls._rabbitmq_publisher