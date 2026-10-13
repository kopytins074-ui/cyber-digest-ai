"""
Модуль формирования предпросмотра письма.
Читает digest.json и создаёт email_preview.txt.
"""

import json
import re
from datetime import datetime


def format_sources(sources):
    """
    Форматирует список источников в читаемый вид.
    
    Аргументы:
        sources (list): список словарей с полями source, url, date, id.
    
    Возвращает:
        str: отформатированный список источников.
    """
    lines = []
    for src in sources:
        source = src.get("source", "Неизвестный источник")
        url = src.get("url", "")
        date = src.get("date", "")
        news_id = src.get("id", "")
        lines.append(f"  • {source} ({date}) — {url} [ID: {news_id}]")
    return "\n".join(lines)


def format_event(event, index):
    """
    Форматирует одно событие для письма.
    
    Аргументы:
        event (dict): событие с полями title, summary, consequences, sources, reasoning.
        index (int): порядковый номер события.
    
    Возвращает:
        str: отформатированный текст события.
    """
    title = event.get("title", "Без заголовка")
    summary = event.get("summary", "")
    consequences = event.get("consequences", "")
    sources = event.get("sources", [])
    reasoning = event.get("reasoning", "")
    
    text = f"""
{index}. {title}

   Суть: {summary}

   Последствия: {consequences}

   Источники:
{format_sources(sources)}

   Обоснование выбора: {reasoning}
"""
    return text


def format_period(period):
    """
    Форматирует период в читаемый вид.
    
    Аргументы:
        period (dict): словарь с полями start и end (ISO-формат).
    
    Возвращает:
        str: отформатированный период.
    """
    start = period.get("start", "")
    end = period.get("end", "")
    
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        return f"с {start_dt.strftime('%d.%m.%Y %H:%M')} по {end_dt.strftime('%d.%m.%Y %H:%M')} (МСК)"
    except (ValueError, TypeError):
        return f"с {start} по {end}"


def count_chars_without_urls(text):
    """
    Считает символы в тексте без учёта URL.
    
    Аргументы:
        text (str): текст для подсчёта.
    
    Возвращает:
        int: количество символов без URL.
    """
    text_without_urls = re.sub(r'https?://\S+', '', text)
    return len(text_without_urls)


def truncate_to_limit(text, limit=4000):
    """
    Обрезает текст до лимита, сохраняя целостность предложений.
    
    Аргументы:
        text (str): текст для обрезки.
        limit (int): максимальная длина (по умолчанию 4000).
    
    Возвращает:
        str: обрезанный текст.
    """
    if count_chars_without_urls(text) <= limit:
        return text
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = count_chars_without_urls(sentence)
        if current_length + sentence_length > limit:
            break
        result.append(sentence)
        current_length += sentence_length
    
    return " ".join(result)


def build_email_preview(digest):
    """
    Формирует текст письма из дайджеста.
    
    Аргументы:
        digest (dict): дайджест с полями period и events.
    
    Возвращает:
        tuple: (тема письма, тело письма).
    """
    period = digest.get("period", {})
    events = digest.get("events", [])
    
    period_text = format_period(period)
    subject = f"Дайджест по кибербезопасности: {period_text}"
    
    body_parts = [
        "=" * 60,
        "ДАЙДЖЕСТ ПО КИБЕРБЕЗОПАСНОСТИ",
        "=" * 60,
        "",
        f"Тема: {subject}",
        f"Период: {period_text}",
        f"Событий в выпуске: {len(events)}",
    ]
    
    if len(events) < 5:
        body_parts.append(f"Причина: найдено только {len(events)} событий, соответствующих критериям отбора.")
    
    body_parts.extend([
        "",
        "=" * 60,
        "",
    ])
    
    if not events:
        body_parts.append("За указанный период событий по теме кибербезопасности не найдено.")
    else:
        for i, event in enumerate(events, 1):
            body_parts.append(format_event(event, i))
            body_parts.append("-" * 60)
    
    body_parts.append("")
    body_parts.append("Конец дайджеста.")
    
    body = "\n".join(body_parts)
    current_length = count_chars_without_urls(body)
    print(f"Длина письма (без URL): {current_length} знаков")
    
    if current_length > 4000:
        print(f"Письмо превышает лимит 4000 знаков. Обрезаем...")
        body = truncate_to_limit(body, 4000)
        print(f"Новая длина: {count_chars_without_urls(body)} знаков")
    
    return subject, body


def save_email_preview(subject, body, filepath="email_preview.txt"):
    """
    Сохраняет предпросмотр письма в файл.
    
    Аргументы:
        subject (str): тема письма.
        body (str): тело письма.
        filepath (str): путь к файлу (по умолчанию email_preview.txt).
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"ТЕМА: {subject}\n")
        f.write("\n")
        f.write(body)
    print(f"Предпросмотр письма сохранён в {filepath}")


if __name__ == "__main__":
    with open("digest.json", "r", encoding="utf-8") as f:
        digest = json.load(f)
    
    subject, body = build_email_preview(digest)
    save_email_preview(subject, body)
    
    print("\n" + "=" * 60)
    print(body)