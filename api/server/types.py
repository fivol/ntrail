from enum import Enum


class ResponseVerbose(Enum):
    """Уровень детализации информации в запросе"""
    # Параметр по умолчанию, возвращать среднее количество информации
    normal = 'normal'
    # Упрощенный запрос, только необходимый минимум
    simple = 'simple'
    # Подробная инфа по запросу
    detail = 'detail'
