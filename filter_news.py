"""
Модуль фильтрации новостей по времени.
Оставляет только новости за последние 24 часа (московское время).
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Московский часовой пояс
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Текущее время и граница 24-часового окна
NOW = datetime.now(MOSCOW_TZ)
START_TIME = NOW - timedelta(hours=24)


def parse_date(date_str):
    """
    Преобразует строку с датой в объект datetime с московским часовым поясом.
    
    Поддерживаемые форматы:
        - %Y-%m-%d %H:%M:%S  (2026-10-12 10:00:00)
        - %Y-%m-%dT%H:%M:%S  (2026-10-12T10:00:00)
        - %Y-%m-%d %H:%M     (2026-10-12 10:00)
        - %d.%m.%Y %H:%M     (12.10.2026 10:00)
    
    Аргументы:
        date_str (str): строка с датой.
    
    Возвращает:
        datetime | None: объект datetime с московским поясом или None,
                         если дату не удалось распознать.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.replace(tzinfo=MOSCOW_TZ)
        except ValueError:
            continue
    
    return None


def filter_by_time(news_list):
    """
    Фильтрует новости по времени: оставляет только те, что за последние 24 часа.
    
    Аргументы:
        news_list (list): список словарей с новостями.
    
    Возвращает:
        tuple: (отфильтрованные новости, журнал исключённых с причинами).
    """
    filtered = []
    excluded_log = []
    
    for news in news_list:
        news_date = parse_date(news.get("date"))
        
        # Если дату не удалось распознать — в журнал исключённых
        if news_date is None:
            excluded_log.append({
                "id": news.get("id"),
                "reason": "Дата отсутствует или не распознана"
            })
            continue
        
        # Проверяем, попадает ли дата в 24-часовое окно
        if START_TIME <= news_date <= NOW:
            filtered.append(news)
        else:
            excluded_log.append({
                "id": news.get("id"),
                "reason": f"Дата {news_date} вне периода ({START_TIME} — {NOW})"
            })
    
    return filtered, excluded_log