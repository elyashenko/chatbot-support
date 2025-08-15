from typing import List, Dict, Any, Optional
import json
import time
from loguru import logger
from ..core.config import settings
from ..core.llm_providers import llm_manager
from .vector_store import vector_store_manager


class RAGEngine:
    """Основной RAG движок для обработки запросов"""
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Возвращает системный промпт для чат-бота"""
        return """Ты - помощник поддержки разработчиков. Твоя задача - помогать разработчикам решать технические вопросы, связанные с:

1. CI/CD процессами и пайплайнами
2. Разработкой и деплоем приложений
3. Работой с базами данных и API
4. Отладкой и решением проблем
5. Лучшими практиками разработки

Используй предоставленный контекст для формирования точных и полезных ответов. Если в контексте нет информации для ответа, честно скажи об этом и предложи обратиться к команде поддержки.

Отвечай на русском языке, если вопрос задан на русском, и на английском, если вопрос задан на английском.

Форматируй ответы с использованием Markdown для лучшей читаемости кода и команд."""
    
    async def process_query(self, query: str, session_context: List[Dict[str, str]] = None,
                          user_role: str = "developer", preferred_model: str = None) -> Dict[str, Any]:
        """Обрабатывает пользовательский запрос с использованием RAG"""
        start_time = time.time()
        
        try:
            # 1. Поиск релевантного контекста
            context_results = await self._retrieve_context(query, user_role)
            
            # 2. Формирование промпта с контекстом
            messages = self._build_messages(query, context_results, session_context)
            
            # 3. Генерация ответа
            llm_response = await llm_manager.generate_response(
                messages=messages,
                preferred_model=preferred_model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            
            # 4. Подготовка результата
            response_time = time.time() - start_time
            
            result = {
                "content": llm_response.get("content"),
                "model_used": llm_response.get("model"),
                "tokens_used": llm_response.get("tokens_used", 0),
                "response_time": response_time,
                "context_sources": self._format_context_sources(context_results),
                "similarity_scores": self._format_similarity_scores(context_results),
                "success": llm_response.get("success", False)
            }
            
            if not llm_response.get("success"):
                result["error"] = llm_response.get("error", "Неизвестная ошибка")
            
            logger.info(f"RAG запрос обработан за {response_time:.2f}с, модель: {result['model_used']}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки RAG запроса: {str(e)}")
            return {
                "content": "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже.",
                "model_used": "error",
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def _retrieve_context(self, query: str, user_role: str) -> List[Dict[str, Any]]:
        """Извлекает релевантный контекст для запроса"""
        try:
            # Фильтр по роли пользователя (если нужно)
            filter_metadata = None
            if user_role != "developer":
                filter_metadata = {"user_role": user_role}
            
            # Поиск в векторной базе
            context_results = await vector_store_manager.search_relevant_context(
                query=query,
                filter_metadata=filter_metadata,
                n_results=settings.top_k_results
            )
            
            return context_results
        except Exception as e:
            logger.error(f"Ошибка извлечения контекста: {str(e)}")
            return []
    
    def _build_messages(self, query: str, context_results: List[Dict[str, Any]], 
                       session_context: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Формирует сообщения для LLM с контекстом"""
        messages = []
        
        # Системный промпт
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Добавляем контекст, если есть
        if context_results:
            context_text = self._format_context_for_prompt(context_results)
            messages.append({
                "role": "system",
                "content": f"Контекст для ответа:\n\n{context_text}\n\nИспользуй эту информацию для формирования ответа."
            })
        
        # Добавляем историю сессии
        if session_context:
            messages.extend(session_context)
        
        # Добавляем текущий запрос
        messages.append({
            "role": "user",
            "content": query
        })
        
        return messages
    
    def _format_context_for_prompt(self, context_results: List[Dict[str, Any]]) -> str:
        """Форматирует контекст для промпта"""
        if not context_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(context_results, 1):
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            similarity = result.get("similarity", 0)
            
            # Добавляем метаданные источника
            source_info = ""
            if metadata.get("title"):
                source_info += f"Источник: {metadata['title']}"
            if metadata.get("source_url"):
                source_info += f" ({metadata['source_url']})"
            
            context_parts.append(f"--- Документ {i} (сходство: {similarity:.2f}) ---")
            if source_info:
                context_parts.append(f"{source_info}")
            context_parts.append(f"{text}\n")
        
        return "\n".join(context_parts)
    
    def _format_context_sources(self, context_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Форматирует источники контекста для ответа"""
        sources = []
        for result in context_results:
            metadata = result.get("metadata", {})
            sources.append({
                "id": result.get("id"),
                "title": metadata.get("title", "Неизвестный источник"),
                "url": metadata.get("source_url"),
                "similarity": result.get("similarity", 0)
            })
        return sources
    
    def _format_similarity_scores(self, context_results: List[Dict[str, Any]]) -> List[float]:
        """Форматирует оценки сходства"""
        return [result.get("similarity", 0) for result in context_results]


class ConversationManager:
    """Менеджер для управления диалогами"""
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.max_context_length = 10  # Максимальное количество сообщений в контексте
    
    async def process_conversation(self, user_message: str, session_id: str,
                                 user_role: str = "developer", 
                                 conversation_history: List[Dict[str, str]] = None,
                                 preferred_model: str = None) -> Dict[str, Any]:
        """Обрабатывает сообщение в контексте диалога"""
        try:
            # Подготавливаем контекст диалога
            session_context = self._prepare_session_context(conversation_history)
            
            # Обрабатываем запрос через RAG
            response = await self.rag_engine.process_query(
                query=user_message,
                session_context=session_context,
                user_role=user_role,
                preferred_model=preferred_model
            )
            
            # Добавляем информацию о сессии
            response["session_id"] = session_id
            response["timestamp"] = time.time()
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка обработки диалога: {str(e)}")
            return {
                "content": "Извините, произошла ошибка при обработке сообщения.",
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }
    
    def _prepare_session_context(self, conversation_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Подготавливает контекст сессии для LLM"""
        if not conversation_history:
            return []
        
        # Ограничиваем длину контекста
        recent_messages = conversation_history[-self.max_context_length:]
        
        # Фильтруем только user и assistant сообщения
        filtered_messages = []
        for msg in recent_messages:
            if msg.get("role") in ["user", "assistant"]:
                filtered_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return filtered_messages
    
    def update_conversation_history(self, history: List[Dict[str, str]], 
                                  user_message: str, assistant_response: str) -> List[Dict[str, str]]:
        """Обновляет историю диалога"""
        updated_history = history.copy() if history else []
        
        # Добавляем сообщение пользователя
        updated_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": time.time()
        })
        
        # Добавляем ответ ассистента
        updated_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": time.time()
        })
        
        # Ограничиваем длину истории
        if len(updated_history) > self.max_context_length * 2:
            updated_history = updated_history[-self.max_context_length * 2:]
        
        return updated_history


class RAGPipeline:
    """Полный RAG пайплайн"""
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.conversation_manager = ConversationManager()
    
    async def process_user_query(self, query: str, session_id: str,
                               user_role: str = "developer",
                               conversation_history: List[Dict[str, str]] = None,
                               preferred_model: str = None) -> Dict[str, Any]:
        """Основной метод для обработки пользовательского запроса"""
        return await self.conversation_manager.process_conversation(
            user_message=query,
            session_id=session_id,
            user_role=user_role,
            conversation_history=conversation_history,
            preferred_model=preferred_model
        )
    
    async def add_knowledge_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Добавляет документы в базу знаний"""
        return await vector_store_manager.add_knowledge_documents(documents)
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Возвращает статистику векторной базы"""
        return vector_store_manager.get_stats()
    
    def get_available_models(self) -> List[str]:
        """Возвращает список доступных моделей"""
        return llm_manager.get_available_models()


# Глобальный экземпляр RAG пайплайна
rag_pipeline = RAGPipeline()
