from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/chatbot_support"
    
    # Vector Database
    chroma_persist_directory: str = "./data/chroma_db"
    
    # AI Models Configuration
    gigachat_api_key: Optional[str] = None
    gigachat_base_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    gigachat_verify_ssl_cert: bool = False
    
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Model Settings
    default_model: str = "gigachat"
    fallback_models: List[str] = ["deepseek", "openai"]
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Confluence Integration
    confluence_url: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_space_keys: List[str] = ["DEV", "TECH", "SUPPORT"]
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/chatbot.log"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # RAG Settings
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def get_available_models() -> List[str]:
    """Возвращает список доступных моделей на основе настроенных API ключей"""
    available_models = []
    
    if settings.gigachat_api_key:
        available_models.append("gigachat")
    
    if settings.deepseek_api_key:
        available_models.append("deepseek")
    
    if settings.openai_api_key:
        available_models.append("openai")
    
    return available_models


def validate_model_configuration() -> bool:
    """Проверяет корректность конфигурации моделей"""
    available_models = get_available_models()
    
    if not available_models:
        raise ValueError("Не настроен ни один API ключ для AI моделей")
    
    if settings.default_model not in available_models:
        raise ValueError(f"Модель по умолчанию '{settings.default_model}' недоступна")
    
    return True
