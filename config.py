import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 100
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    gigachat_model: str = "GigaChat"
    temperature: float = 0.7
    token_cost: float = 25000 / 125000000
    telegram_token: str = os.getenv("TELEGRAM_TOKEN")
    gigachat_api_key: str = os.getenv("GIGACHAT_API_KEY")
    document_url: str = os.getenv("DOCUMENT_URL")
    chat_log_path: str = os.getenv("CHAT_LOG_PATH", "chat_logs.csv")

    def validate(self):
        """Проверка наличия обязательных переменных окружения"""
        if not self.telegram_token:
            raise ValueError("TELEGRAM_TOKEN is missing or invalid!")
        if not self.gigachat_api_key:
            raise ValueError("GIGACHAT_API_KEY is missing or invalid!")
        if not self.document_url:
            raise ValueError("DOCUMENT_URL is missing or invalid!")