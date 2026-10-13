"""
Модуль логирования.
Собирает информацию о том, что произошло с каждой новостью,
и сохраняет её в processing_log.csv и ai_usage.json.
"""

import csv
import json
from datetime import datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


class ProcessingLogger:
    """Логгер для отслеживания обработки новостей."""
    
    def __init__(self):
        self.records = []
        self.ai_calls = 0
        self.ai_input_tokens = 0
        self.ai_output_tokens = 0
    
    def log(self, news_id, stage, status, reason=""):
        """
        Записывает событие в лог.
        
        Аргументы:
            news_id: ID новости.
            stage: этап обработки (time_filter, topic_filter, validation).
            status: статус (passed, excluded).
            reason: причина (если исключена).
        """
        self.records.append({
            "news_id": news_id,
            "stage": stage,
            "status": status,
            "reason": reason,
            "timestamp": datetime.now(MOSCOW_TZ).isoformat()
        })
    
    def log_ai_call(self, input_tokens=0, output_tokens=0):
        """Записывает вызов к ИИ."""
        self.ai_calls += 1
        self.ai_input_tokens += input_tokens
        self.ai_output_tokens += output_tokens
    
    def save_processing_log(self, filepath="processing_log.csv"):
        """Сохраняет лог обработки в CSV-файл."""
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["news_id", "stage", "status", "reason", "timestamp"])
            writer.writeheader()
            writer.writerows(self.records)
        print(f"Лог обработки сохранён в {filepath}")
    
    def save_ai_usage(self, filepath="ai_usage.json"):
        """Сохраняет статистику использования ИИ."""
        data = {
            "ai_calls": self.ai_calls,
            "ai_input_tokens": self.ai_input_tokens,
            "ai_output_tokens": self.ai_output_tokens,
            "total_tokens": self.ai_input_tokens + self.ai_output_tokens,
            "generated_at": datetime.now(MOSCOW_TZ).isoformat()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Статистика ИИ сохранена в {filepath}")


# Глобальный логгер
logger = ProcessingLogger()