from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
import json
import time
from loguru import logger
from .config import settings


class LLMProvider(ABC):
    """Абстрактный базовый класс для LLM провайдеров"""
    
    def __init__(self, api_key: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Генерирует ответ от LLM модели"""
        pass
    
    @abstractmethod
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Форматирует сообщения для конкретного провайдера"""
        pass


class GigaChatProvider(LLMProvider):
    """Провайдер для GigaChat API"""
    
    def __init__(self, api_key: str, base_url: str, verify_ssl: bool = False):
        super().__init__(api_key, base_url)
        self.verify_ssl = verify_ssl
        self.access_token = None
    
    async def _get_access_token(self) -> str:
        """Получает access token для GigaChat"""
        if self.access_token:
            return self.access_token
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "scope": "GIGACHAT_API_PERS"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth",
                headers=headers,
                data=data,
                ssl=self.verify_ssl
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result.get("access_token")
                    return self.access_token
                else:
                    raise Exception(f"Ошибка получения токена: {response.status}")
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Форматирует сообщения для GigaChat"""
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return formatted_messages
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Генерирует ответ от GigaChat"""
        start_time = time.time()
        
        try:
            access_token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": self.format_messages(messages),
                "temperature": kwargs.get("temperature", settings.temperature),
                "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    ssl=self.verify_ssl
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_time = time.time() - start_time
                        
                        return {
                            "content": result["choices"][0]["message"]["content"],
                            "model": "gigachat",
                            "tokens_used": result["usage"]["total_tokens"],
                            "response_time": response_time,
                            "success": True
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"GigaChat API error: {response.status} - {error_text}")
                        raise Exception(f"GigaChat API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Ошибка GigaChat: {str(e)}")
            return {
                "content": None,
                "model": "gigachat",
                "error": str(e),
                "success": False
            }


class DeepSeekProvider(LLMProvider):
    """Провайдер для DeepSeek API"""
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Форматирует сообщения для DeepSeek"""
        return messages  # DeepSeek использует стандартный формат
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Генерирует ответ от DeepSeek"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": self.format_messages(messages),
                "temperature": kwargs.get("temperature", settings.temperature),
                "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_time = time.time() - start_time
                        
                        return {
                            "content": result["choices"][0]["message"]["content"],
                            "model": "deepseek",
                            "tokens_used": result["usage"]["total_tokens"],
                            "response_time": response_time,
                            "success": True
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                        raise Exception(f"DeepSeek API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Ошибка DeepSeek: {str(e)}")
            return {
                "content": None,
                "model": "deepseek",
                "error": str(e),
                "success": False
            }


class OpenAIProvider(LLMProvider):
    """Провайдер для OpenAI API"""
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Форматирует сообщения для OpenAI"""
        return messages  # OpenAI использует стандартный формат
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Генерирует ответ от OpenAI"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": self.format_messages(messages),
                "temperature": kwargs.get("temperature", settings.temperature),
                "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_time = time.time() - start_time
                        
                        return {
                            "content": result["choices"][0]["message"]["content"],
                            "model": "openai",
                            "tokens_used": result["usage"]["total_tokens"],
                            "response_time": response_time,
                            "success": True
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        raise Exception(f"OpenAI API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Ошибка OpenAI: {str(e)}")
            return {
                "content": None,
                "model": "openai",
                "error": str(e),
                "success": False
            }


class LLMManager:
    """Менеджер для работы с несколькими LLM провайдерами"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Инициализирует доступные провайдеры"""
        if settings.gigachat_api_key:
            self.providers["gigachat"] = GigaChatProvider(
                api_key=settings.gigachat_api_key,
                base_url=settings.gigachat_base_url,
                verify_ssl=settings.gigachat_verify_ssl_cert
            )
        
        if settings.deepseek_api_key:
            self.providers["deepseek"] = DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
        
        if settings.openai_api_key:
            self.providers["openai"] = OpenAIProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
    
    async def generate_response(self, messages: List[Dict[str, str]], 
                              preferred_model: str = None, **kwargs) -> Dict[str, Any]:
        """Генерирует ответ, используя предпочтительную модель или fallback"""
        
        # Определяем порядок моделей для попыток
        if preferred_model and preferred_model in self.providers:
            model_order = [preferred_model] + [
                model for model in settings.fallback_models 
                if model in self.providers and model != preferred_model
            ]
        else:
            model_order = [settings.default_model] + [
                model for model in settings.fallback_models 
                if model in self.providers and model != settings.default_model
            ]
        
        # Пытаемся получить ответ от каждой модели
        for model_name in model_order:
            if model_name not in self.providers:
                continue
            
            logger.info(f"Попытка генерации ответа с моделью: {model_name}")
            
            try:
                provider = self.providers[model_name]
                result = await provider.generate_response(messages, **kwargs)
                
                if result["success"]:
                    logger.info(f"Успешный ответ от модели {model_name}")
                    return result
                else:
                    logger.warning(f"Ошибка модели {model_name}: {result.get('error')}")
            
            except Exception as e:
                logger.error(f"Исключение при работе с моделью {model_name}: {str(e)}")
                continue
        
        # Если все модели недоступны
        return {
            "content": "Извините, в данный момент сервис недоступен. Попробуйте позже.",
            "model": "fallback",
            "error": "Все модели недоступны",
            "success": False
        }
    
    def get_available_models(self) -> List[str]:
        """Возвращает список доступных моделей"""
        return list(self.providers.keys())


# Глобальный экземпляр менеджера
llm_manager = LLMManager()
