"""
Модуль генерации текста для каждого события.
Использует ИИ для написания заголовка, сути и последствий.
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

EVENT_PROMPT = """Ты — редактор дайджеста по кибербезопасности. Напиши краткое описание события на основе новостей.

СТРОГИЕ ЗАПРЕТЫ:
- НЕ упоминай даты (числа месяца, годы).
- НЕ упоминай время.
- НЕ выдумывай факты, которых нет в новостях.

Требования:
1. Заголовок: опиши событие без преувеличений (до 100 символов).
2. Суть: изложи факты в 2–3 предложениях.
3. Последствия: укажи, кого затронуло событие и что изменилось. Если данных нет — напиши "Сведений о последствиях нет".

Верни ответ СТРОГО в формате JSON:
{{
  "title": "заголовок",
  "summary": "суть события",
  "consequences": "последствия"
}}

Новости о событии:
{news_text}
"""


def format_group_for_prompt(group):
    """
    Собирает текст всех новостей в группе для промпта.
    
    Аргументы:
        group (list): список новостей об одном событии.
    
    Возвращает:
        str: текст с новостями для отправки в ИИ.
    """
    lines = []
    for news in group:
        title = news.get("title", "")
        text = news.get("text", "")[:1000]
        source = news.get("source", "")
        date = news.get("date", "")
        lines.append(f"Заголовок: {title}\nИсточник: {source}\nДата: {date}\nТекст: {text}\n")
    return "\n---\n".join(lines)


def generate_event_text(group):
    """
    Генерирует текст для одного события с помощью ИИ.
    
    Аргументы:
        group (list): список новостей об одном событии.
    
    Возвращает:
        dict: словарь с полями title, summary, consequences.
    """
    news_text = format_group_for_prompt(group)
    prompt = EVENT_PROMPT.format(news_text=news_text)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
            extra_body={"thinking": {"type": "disabled"}}
        )
        
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
        return {
            "title": data.get("title", group[0].get("title", "")),
            "summary": data.get("summary", ""),
            "consequences": data.get("consequences", "Сведений о последствиях нет")
        }
    
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return {
            "title": group[0].get("title", ""),
            "summary": "Ошибка генерации текста",
            "consequences": "Сведений о последствиях нет"
        }
    except Exception as e:
        print(f"Ошибка API: {e}")
        return {
            "title": group[0].get("title", ""),
            "summary": "Ошибка генерации текста",
            "consequences": "Сведений о последствиях нет"
        }