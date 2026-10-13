"""
Модуль объединения новостей об одном событии.
Использует ИИ для группировки новостей по смыслу.
"""

import json
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, TIMEOUT
from logger import logger

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=TIMEOUT
)

PROMPT = """Ты — редактор дайджеста по кибербезопасности. Тебе дан список новостей.

Сгруппируй новости, которые описывают ОДНО И ТО ЖЕ событие. Новости об одном событии должны попасть в одну группу.

Правила:
- Если две новости описывают одно событие (например, «взлом банка» и «банк подтвердил утечку») — объедини их.
- Если новость просто упоминает другую тему, но описывает ДРУГОЕ событие — не объединяй.
- Если новость уникальна — она образует группу из одного элемента.

Верни ответ СТРОГО в формате JSON, без пояснений:
{{
  "groups": [
    {{"ids": [1, 2], "event_title": "краткое название события"}},
    {{"ids": [3], "event_title": "краткое название события"}}
  ]
}}

Новости:
{news_text}
"""


def format_news_for_prompt(news_list):
    """
    Собирает все новости в текст для промпта.
    
    Аргументы:
        news_list (list): список словарей с новостями.
    
    Возвращает:
        str: текст с новостями для отправки в ИИ.
    """
    lines = []
    for news in news_list:
        news_id = news.get("id", "?")
        title = news.get("title", "")
        text = news.get("text", "")[:500]
        lines.append(f"ID {news_id}: {title}\n{text}\n")
    return "\n---\n".join(lines)


def deduplicate_news(news_list):
    """
    Группирует новости по событиям с помощью ИИ.
    
    Аргументы:
        news_list (list): список словарей с новостями.
    
    Возвращает:
        list: список групп, где каждая группа — список новостей об одном событии.
    """
    if not news_list:
        return []
    
    if len(news_list) == 1:
        return [news_list]
    
    news_text = format_news_for_prompt(news_list)
    prompt = PROMPT.format(news_text=news_text)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0,
            extra_body={"thinking": {"type": "disabled"}}
        )
        
        # Считаем токены
        if response.usage:
            logger.log_ai_call(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )
        
        answer = response.choices[0].message.content.strip()
        
        # Убираем markdown-обёртку, если есть
        if answer.startswith("```"):
            answer = answer.split("```")[1]
            if answer.startswith("json"):
                answer = answer[4:]
        
        data = json.loads(answer)
        groups_data = data.get("groups", [])
        
        # Создаём словарь: id -> новость
        news_by_id = {n.get("id"): n for n in news_list}
        
        # Собираем группы
        result = []
        used_ids = set()
        
        for group_info in groups_data:
            ids = group_info.get("ids", [])
            group = []
            for news_id in ids:
                if news_id in news_by_id and news_id not in used_ids:
                    group.append(news_by_id[news_id])
                    used_ids.add(news_id)
            if group:
                result.append(group)
        
        # Добавляем новости, которые ИИ не включил ни в одну группу
        for news in news_list:
            if news.get("id") not in used_ids:
                result.append([news])
        
        return result
    
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON в дедубликации: {e}")
        print(f"Ответ ИИ: {answer[:500]}")
        return [[news] for news in news_list]
    except Exception as e:
        print(f"Ошибка API в дедубликации: {e}")
        return [[news] for news in news_list]