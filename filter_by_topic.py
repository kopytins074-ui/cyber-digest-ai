"""
Модуль фильтрации новостей по теме.
Определяет, относится ли новость к кибербезопасности, с помощью ИИ.
"""

from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, TIMEOUT
from logger import logger

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=TIMEOUT
)

PROMPT_TEMPLATE = """Ты — эксперт по кибербезопасности. Твоя задача — определить, относится ли новость к теме кибербезопасности.

Кибербезопасность — это всё, что связано с:
- защитой информации
- взломами и утечками данных
- вирусами, фишингом, вредоносным ПО
- атаками на компании и государственные структуры
- законами о персональных данных и защите информации

НЕ относится к кибербезопасности:
- обычные кражи, грабежи, пожары
- политические новости без кибер-контекста
- бытовые происшествия

Ответь строго одним словом: "Да" или "Нет". Без пояснений.

Заголовок: {title}
Текст: {text}
"""


def is_cybersecurity_news(news_item):
    """
    Определяет, относится ли новость к теме кибербезопасности.
    
    Аргументы:
        news_item (dict): словарь с полями title и text.
    
    Возвращает:
        bool: True, если новость по теме, иначе False.
    """
    title = news_item.get("title", "")
    text = news_item.get("text", "")
    
    text_short = text[:2000]
    prompt = PROMPT_TEMPLATE.format(title=title, text=text_short)
    
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
        
        content = response.choices[0].message.content
        if content is None:
            print(f"  [!] API вернул пустой ответ для новости {news_item.get('id')}")
            return False
        answer = content.strip().lower()
        return answer.startswith("да")
    except Exception as e:
        print(f"Ошибка при запросе к ИИ: {e}")
        return False


def filter_by_topic(news_list):
    """
    Фильтрует новости по теме кибербезопасности.
    
    Аргументы:
        news_list (list): список словарей с новостями.
    
    Возвращает:
        tuple: (подходящие новости, журнал исключённых с причинами).
    """
    filtered = []
    excluded_log = []
    
    for news in news_list:
        if is_cybersecurity_news(news):
            filtered.append(news)
        else:
            excluded_log.append({
                "id": news.get("id"),
                "reason": "Не относится к теме кибербезопасности"
            })
    
    return filtered, excluded_log