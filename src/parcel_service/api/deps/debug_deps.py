from src.parcel_service.application.use_cases.debug.debug_recalculate import DebugRecalculateUseCase


def get_uc_debug_recalculate() -> DebugRecalculateUseCase:
    """
    Use case для отладки перерасчёта стоимости доставки.

    :return: Экземпляр use case для отладочного перерасчёта.
    :rtype: DebugRecalculateUseCase
    """
    return DebugRecalculateUseCase()