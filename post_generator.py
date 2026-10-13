"""
Модуль генерации поста для соцсетей.
Читает digest.json и создаёт post.txt.
"""

import json
import re
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, TIMEOUT
from logger import logger

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=TIMEOUT
)

PROMPT = """Ты — редактор Telegram-канала по кибербезопасности. Напиши короткий пост на основе событий.

Стиль:
- Живой, но деловой. Как будто рассказываешь коллеге.
- Начни с короткого вступления (1 предложение): «Главное за сутки: ...».
- Для каждого события — 1–2 предложения: что произошло, кого затронуло.
- В конце — короткий вывод или призыв к действию.
- Ссылки вставляй прямо в текст, а не отдельной строкой.
- НЕ пиши заголовок «Дайджест событий кибербезопасности» — начни сразу с вступления.

Требования:
1. Длина: не более 2000 символов с пробелами (без учёта URL).
2. Сохрани ВСЕ события из списка.
3. Обязательно указывай ссылки в полном формате (с https://).
4. Без эмодзи.
5. Не выдумывай факты, числа, даты. Используй только то, что есть в событиях.
6. НЕ упоминай конкретные даты и время.

События:
{events_text}

Верни только текст поста, без пояснений.
"""


def format_events_for_post(digest):
    """
    Собирает события из дайджеста в текст для промпта.
    
    Аргументы:
        digest (dict): дайджест с полем events.
    
    Возвращает:
        str: текст с событиями для отправки в ИИ.
    """
    lines = []
    for i, event in enumerate(digest.get("events", []), 1):
        title = event.get("title", "")
        summary = event.get("summary", "")
        sources = event.get("sources", [])
        urls = ", ".join([s.get("url", "") for s in sources])
        lines.append(f"{i}. {title}\n{summary}\nСсылки: {urls}\n")
    return "\n".join(lines)


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


def truncate_to_limit(text, limit=2000):
    """
    Обрезает текст до лимита, сохраняя целостность предложений.
    
    Аргументы:
        text (str): текст для обрезки.
        limit (int): максимальная длина (по умолчанию 2000).
    
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


def generate_post(digest):
    """
    Генерирует текст поста через ИИ.
    
    Аргументы:
        digest (dict): дайджест с полем events.
    
    Возвращает:
        str | None: текст поста или None при ошибке.
    """
    events_text = format_events_for_post(digest)
    prompt = PROMPT.format(events_text=events_text)
    
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
        
        post_text = response.choices[0].message.content.strip()
        
        current_length = count_chars_without_urls(post_text)
        print(f"Длина поста (без URL): {current_length} знаков")
        
        if current_length > 2000:
            print(f"Пост превышает лимит. Обрезаем до 2000 знаков...")
            post_text = truncate_to_limit(post_text, 2000)
            print(f"Новая длина: {count_chars_without_urls(post_text)} знаков")
        
        return post_text
    except Exception as e:
        print(f"Ошибка генерации поста: {e}")
        return None


def save_post(post_text, filepath="post.txt"):
    """
    Сохраняет пост в файл.
    
    Аргументы:
        post_text (str): текст поста.
        filepath (str): путь к файлу (по умолчанию post.txt).
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(post_text)
    print(f"Пост сохранён в {filepath}")


if __name__ == "__main__":
    with open("digest.json", "r", encoding="utf-8") as f:
        digest = json.load(f)
    
    post = generate_post(digest)
    if post:
        save_post(post)
        print("\n" + "=" * 60)
        print(post)