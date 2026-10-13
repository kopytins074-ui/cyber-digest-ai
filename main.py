"""
Главный модуль проекта.
Собирает все этапы обработки новостей в единый конвейер.
"""

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from filter_news import filter_by_time
from filter_by_topic import filter_by_topic
from deduplicate_news import deduplicate_news
from select_top5 import select_top5
from generate_digest import generate_event_text
from validate import validate_digest
from logger import logger


def load_news(filepath):
    """
    Загружает список новостей из JSON-файла.
    
    Аргументы:
        filepath (str): путь к файлу с новостями.
    
    Возвращает:
        list: список словарей с новостями.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_digest(news_list):
    """
    Главный конвейер: от сырых новостей до готового дайджеста.
    
    Этапы:
        1. Фильтрация по времени (24 часа).
        2. Фильтрация по теме (ИИ).
        3. Объединение новостей об одном событии (ИИ).
        4. Отбор топ-5 событий (ИИ).
        5. Генерация текста для каждого события (ИИ).
        6. Валидация (проверка чисел).
    
    Аргументы:
        news_list (list): список новостей.
    
    Возвращает:
        dict: готовый дайджест.
    """
    # ШАГ 1: Фильтрация по времени
    print("=" * 50)
    print("ШАГ 1: Фильтрация по времени")
    news_by_time, excluded_time = filter_by_time(news_list)
    print(f"  Прошло: {len(news_by_time)}, исключено: {len(excluded_time)}")
    
    # Логирование ШАГА 1
    for news in news_by_time:
        logger.log(news.get("id"), "time_filter", "passed")
    for item in excluded_time:
        logger.log(item.get("id"), "time_filter", "excluded", item.get("reason", ""))
    
    # ШАГ 2: Фильтрация по теме
    print("\nШАГ 2: Фильтрация по теме (ИИ)")
    news_by_topic, excluded_topic = filter_by_topic(news_by_time)
    print(f"  Прошло: {len(news_by_topic)}, исключено: {len(excluded_topic)}")
    
    # Логирование ШАГА 2
    for news in news_by_topic:
        logger.log(news.get("id"), "topic_filter", "passed")
    for item in excluded_topic:
        logger.log(item.get("id"), "topic_filter", "excluded", item.get("reason", ""))
    
    # ШАГ 3: Объединение дубликатов
    print("\nШАГ 3: Объединение новостей об одном событии")
    groups = deduplicate_news(news_by_topic)
    print(f"  Получено групп (событий): {len(groups)}")
    
    # Логирование ШАГА 3
    for i, group in enumerate(groups, 1):
        group_ids = [n.get("id") for n in group]
        logger.log(f"group_{i}", "deduplication", "grouped", f"Новости: {group_ids}")
    
    # ШАГ 4: Отбор топ-5
    print("\nШАГ 4: Отбор топ-5 событий (ИИ)")
    top_groups, reasoning = select_top5(groups)
    print(f"  Отобрано событий: {len(top_groups)}")
    
    # Логирование ШАГА 4
    selected_ids = [g[0].get("id") for g in top_groups]
    for group in groups:
        event_id = group[0].get("id")
        if event_id in selected_ids:
            logger.log(event_id, "top5_selection", "selected")
        else:
            logger.log(event_id, "top5_selection", "excluded", "Не вошло в топ-5")
    
    # ШАГ 5: Генерация текста
    print("\nШАГ 5: Генерация текста для каждого события")
    digest_events = []
    for group in top_groups:
        event_id = group[0].get("id")
        print(f"  Обработка события {event_id}...")
        event_text = generate_event_text(group)
        
        # Логирование вызова ИИ
        logger.log_ai_call()
        
        sources = []
        for news in group:
            sources.append({
                "source": news.get("source", ""),
                "url": news.get("url", ""),
                "date": news.get("date", ""),
                "id": news.get("id", "")
            })
        
        digest_events.append({
            "title": event_text["title"],
            "summary": event_text["summary"],
            "consequences": event_text["consequences"],
            "sources": sources,
            "reasoning": reasoning.get(str(event_id), "")
        })
    
    # ШАГ 6: Валидация
    print("\nШАГ 6: Валидация")
    all_valid, validation_log = validate_digest(
        {"events": digest_events},
        news_list
    )
    if all_valid:
        print("  [OK] Все события прошли валидацию")
    else:
        print(f"  [!] Найдены ошибки в {len(validation_log)} событиях")
        for item in validation_log:
            logger.log(item.get("event_title"), "validation", "warning", str(item.get("errors")))
    
    # Формирование финального дайджеста
    moscow_tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(moscow_tz)
    
    digest = {
        "period": {
            "start": (now - timedelta(hours=24)).isoformat(),
            "end": now.isoformat()
        },
        "events": digest_events,
        "excluded_log": excluded_time + excluded_topic,
        "validation_log": validation_log,
        "events_count": len(digest_events),
        "events_count_reason": (
            f"Найдено {len(digest_events)} событий. "
            f"Остальные новости исключены по времени или теме."
        )
    }
    
    # Сохранение логов
    logger.save_processing_log()
    logger.save_ai_usage()
    
    return digest


def save_digest(digest, filepath):
    """Сохраняет дайджест в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(digest, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    news = load_news("news.json")
    digest = build_digest(news)
    save_digest(digest, "digest.json")
    
    print("\n" + "=" * 50)
    print("ДАЙДЖЕСТ ГОТОВ! Сохранён в digest.json")
    print(f"Событий в дайджесте: {len(digest['events'])}")