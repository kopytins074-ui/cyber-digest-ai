"""
Модуль отбора топ-5 событий.
Использует ИИ для выбора самых важных событий из списка.
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

PROMPT_TEMPLATE = """Ты — редактор дайджеста по кибербезопасности. Тебе даны события за последние 24 часа.

Выбери 5 самых важных событий по критериям:
1. Масштаб: сколько организаций, систем или людей затронуто.
2. Последствия: что изменилось, какие риски возникли.
3. Срочность: требует ли событие немедленного внимания.

Верни ответ СТРОГО в формате JSON, без пояснений до и после:
{{
  "selected_ids": [список ID выбранных событий],
  "reasoning": {{
    "ID": "краткое обоснование (одно предложение)"
  }}
}}

События:
{events_text}
"""


def format_events(groups):
    """
    Превращает список групп новостей в текст для промпта.
    
    Аргументы:
        groups (list): список групп, где каждая группа — список новостей.
    
    Возвращает:
        str: текст с событиями для отправки в ИИ.
    """
    lines = []
    for group in groups:
        event_id = group[0].get("id", "unknown")
        title = group[0].get("title", "Без заголовка")
        description = group[0].get("text", "")[:300]
        lines.append(f"ID {event_id}: {title}\n{description}\n")
    return "\n".join(lines)


def select_top5(groups):
    """
    Отбирает до 5 самых важных событий с помощью ИИ.
    
    Аргументы:
        groups (list): список групп новостей.
    
    Возвращает:
        tuple: (выбранные группы, словарь с обоснованиями по ID).
    """
    if not groups:
        return [], {}
    
    events_text = format_events(groups)
    prompt = PROMPT_TEMPLATE.format(events_text=events_text)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0,
            extra_body={"thinking": {"type": "disabled"}}
        )
        
        if response.usage:
            logger.log_ai_call(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )
        
        answer = response.choices[0].message.content.strip()
        
        # Убираем markdown-обёртку, если она есть
        if answer.startswith("```"):
            answer = answer.split("```")[1]
            if answer.startswith("json"):
                answer = answer[4:]
        
        data = json.loads(answer)
        selected_ids = data.get("selected_ids", [])
        reasoning = data.get("reasoning", {})
        
        # Отбираем группы по реальным ID новостей
        selected_groups = []
        selected_reasoning = {}
        for group in groups:
            event_id = group[0].get("id")
            if event_id in selected_ids:
                selected_groups.append(group)
                selected_reasoning[str(event_id)] = reasoning.get(str(event_id), "")
        
        return selected_groups, selected_reasoning
    
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        print(f"Ответ ИИ: {answer[:500]}")
        return groups[:5], {}
    except Exception as e:
        print(f"Ошибка при запросе к ИИ: {e}")
        return groups[:5], {}