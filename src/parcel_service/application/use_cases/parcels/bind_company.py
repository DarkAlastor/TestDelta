from loguru import logger
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase, TDeps

from src.parcel_service.domain.interfaces.repository import IParcelRepository
from src.parcel_service.domain.exceptions.domain_error import ParcelAlreadyBoundError, CompanyNotFoundError, ParcelNotFoundError
from src.parcel_service.domain.dto.dto_bind_company import BindCompanyData, BindCompanyResult



class BindCompanyUseCase(IUseCase[BindCompanyData, BindCompanyResult, None]):
    """
    UseCase для привязки компании к посылке, если она ещё не привязана.
    """

    async def __call__(self, dto: BindCompanyData, uow: IUnitOfWork, deps: TDeps = None) -> BindCompanyResult:
        """
        Выполняет привязку компании к посылке.

        :param dto: DTO с идентификатором посылки и компании.
        :type dto: BindCompanyData
        :param uow: Единица работы (Unit of Work) для получения репозитория и управления транзакцией.
        :type uow: IUnitOfWork
        :param deps: Не используется (None).
        :type deps: None
        :return: DTO с результатом операции (успешное сообщение).
        :rtype: BindCompanyResult

        :raises ParcelAlreadyBoundError: Если посылка уже привязана к компании.
        """
        logger.info("BindCompanyUseCase started | parcel_id={} company_id={}", dto.parcel_id, dto.company_id)

        try:
            async with uow:

                repo_parcel = await uow.get_repo(IParcelRepository)
                result = await repo_parcel.bind_company_if_unset(parcel_id=dto.parcel_id, company_id=dto.company_id)

                if result is None:
                    raise ParcelNotFoundError()

                if result:
                    logger.info("Компания успешно привязана | parcel_id={} company_id={}", dto.parcel_id, dto.company_id)
                    return BindCompanyResult()

                raise ParcelAlreadyBoundError()

        except CompanyNotFoundError:
            logger.warning("Компания не найдена | company_id={}", dto.company_id)
            raise

        except ParcelAlreadyBoundError:
            logger.warning("Посылка уже привязана | parcel_id={} company_id={}", dto.parcel_id, dto.company_id)
            raise

        except ParcelNotFoundError:
            logger.warning("Поссылка не найдена | parcel_id={}", dto.parcel_id)
            raise

        except Exception as e:
            logger.error("Непредвиденная ошибка при выборе компании | parcel_id={} error={}", dto.parcel_id, str(e))
            raise
