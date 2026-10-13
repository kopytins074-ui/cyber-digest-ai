"""
Модуль валидации чисел.
Проверяет, что все числа в сгенерированном тексте есть в исходных новостях.
"""

import re


def extract_numbers(text):
    """
    Извлекает все числа из текста (целые и с десятичной точкой).
    
    Аргументы:
        text (str): текст для анализа.
    
    Возвращает:
        set: множество чисел (float).
    """
    if not text:
        return set()
    
    numbers = re.findall(r'\d+(?:[.,]\d+)?', str(text))
    result = set()
    for num in numbers:
        num = num.replace(',', '.')
        try:
            result.add(float(num))
        except ValueError:
            continue
    return result


def validate_event(event, source_news):
    """
    Проверяет, что числа в тексте события есть в исходных новостях.
    
    Аргументы:
        event (dict): событие с полями title, summary, consequences.
        source_news (list): список исходных новостей.
    
    Возвращает:
        tuple: (валидно, список ошибок).
    """
    errors = []
    
    # Собираем числа из текста события
    event_text = " ".join([
        event.get("title", ""),
        event.get("summary", ""),
        event.get("consequences", "")
    ])
    event_numbers = extract_numbers(event_text)
    
    # Собираем числа из исходных новостей (включая даты)
    source_text = " ".join([
        n.get("title", "") + " " + n.get("text", "") + " " + n.get("date", "")
        for n in source_news
    ])
    source_numbers = extract_numbers(source_text)
    
    # Ищем числа в событии, которых нет в источнике
    suspicious = event_numbers - source_numbers
    
    # Исключаем годы (2000-2100)
    suspicious = {n for n in suspicious if not (2000 <= n <= 2100)}
    
    if suspicious:
        errors.append(f"Числа не найдены в источнике: {sorted(suspicious)}")
    
    return len(errors) == 0, errors


def validate_digest(digest, news_list):
    """
    Проверяет все события в дайджесте.
    
    Аргументы:
        digest (dict): дайджест с полем events.
        news_list (list): список исходных новостей.
    
    Возвращает:
        tuple: (все_валидны, журнал_ошибок).
    """
    all_valid = True
    log = []
    
    for event in digest.get("events", []):
        # Находим исходные новости по ID из sources
        source_ids = [s.get("id") for s in event.get("sources", [])]
        source_news = [n for n in news_list if n.get("id") in source_ids]
        
        valid, errors = validate_event(event, source_news)
        
        if not valid:
            all_valid = False
            log.append({
                "event_title": event.get("title", ""),
                "errors": errors
            })
    
    return all_valid, log