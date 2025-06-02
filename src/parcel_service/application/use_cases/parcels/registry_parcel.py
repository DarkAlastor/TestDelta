import json
from uuid import uuid4
from loguru import logger

from src.parcel_service.domain.dto.dto_create_parcel import ParcelData, ParcelResult
from src.parcel_service.domain.interfaces.repository import IOutboxEventRepository
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase, TDeps
from src.parcel_service.infrastructure.db.sql.models import OutboxEvent

from src.parcel_service.domain.exceptions.domain_error import OutboxDuplicateError, OutboxPersistenceError


class RegistryParcelUseCase(IUseCase[ParcelData, ParcelResult, None]):
    """
    UseCase для регистрации новой посылки и записи события в Outbox.

    Сохраняет информацию о новой посылке в виде события в таблице Outbox, чтобы затем передать
    данные в другие сервисы через брокер сообщений.

    :param dto: Данные о посылке.
    :type dto: ParcelData
    :param uow: Единица работы (Unit of Work) для управления транзакцией и получения репозиториев.
    :type uow: IUnitOfWork
    :param deps: Зависимости (не используются в данном UseCase).
    :type deps: None
    :return: Результат с `parcel_id`.
    :rtype: ParcelResult
    """

    async def __call__(self, dto: ParcelData , uow: IUnitOfWork, deps: TDeps = None) -> ParcelResult:
        logger.info("Начало регистрации посылки | parcel_id={} session_id={}", dto.parcel_id, dto.session_id)

        try:
            payload = dto.to_payload()

            # Валидация сериализуемости
            json.dumps(payload)

            outbox_event = OutboxEvent(
                id = str(uuid4()),
                parcel_id = dto.parcel_id,
                session_id = dto.session_id,
                event_type = "parcel.registered",
                payload = dto.to_payload()
            )

            async with uow:
                repo_outbox = await uow.get_repo(repo_type=IOutboxEventRepository)
                await repo_outbox.add(outbox_event)

            logger.info("Событие Outbox успешно добавлено | parcel_id={}", dto.parcel_id)
            return ParcelResult(parcel_id=dto.parcel_id)

        except OutboxDuplicateError:
            logger.warning("Событие уже существует | parcel_id={}", dto.parcel_id)
            return ParcelResult(parcel_id=dto.parcel_id)

        except OutboxPersistenceError:
            logger.error("Ошибка базы данных при регистрации посылки | parcel_id={}", dto.parcel_id)
            raise

        except (TypeError, ValueError) as validation_err:
            logger.warning("Некорректный payload для события | parcel_id={} error={}", dto.parcel_id, str(validation_err))
            raise

        except Exception as e:
            logger.error("Непредвиденная ошибка при регистрации посылки | parcel_id={} error={}", dto.parcel_id, str(e))
            raise
