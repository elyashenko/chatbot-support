from typing import List, Dict, Any, Optional
import uuid
import time
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
from ..core.database import get_db, ChatSession, ChatMessage, User
from ..models.rag_engine import rag_pipeline


class ChatService:
    """Сервис для обработки чат-запросов"""
    
    def __init__(self):
        self.active_sessions = {}  # Кэш активных сессий
    
    async def process_message(self, user_id: int, message: str, 
                            session_id: str = None, preferred_model: str = None) -> Dict[str, Any]:
        """Обрабатывает сообщение пользователя"""
        try:
            # Получаем или создаем сессию
            session = await self._get_or_create_session(user_id, session_id)
            
            # Получаем историю диалога
            conversation_history = await self._get_conversation_history(session.id)
            
            # Обрабатываем через RAG
            response = await rag_pipeline.process_user_query(
                query=message,
                session_id=session.session_id,
                user_role="developer",  # TODO: получать из профиля пользователя
                conversation_history=conversation_history,
                preferred_model=preferred_model
            )
            
            # Сохраняем сообщения в БД
            await self._save_messages(session.id, message, response)
            
            # Обновляем сессию
            await self._update_session(session.id, response.get("model_used"))
            
            return {
                "session_id": session.session_id,
                "response": response.get("content"),
                "model_used": response.get("model_used"),
                "context_sources": response.get("context_sources", []),
                "similarity_scores": response.get("similarity_scores", []),
                "response_time": response.get("response_time", 0),
                "success": response.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {str(e)}")
            return {
                "error": "Произошла ошибка при обработке сообщения",
                "success": False
            }
    
    async def _get_or_create_session(self, user_id: int, session_id: str = None) -> ChatSession:
        """Получает существующую сессию или создает новую"""
        db = next(get_db())
        
        try:
            if session_id:
                # Ищем существующую сессию
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id,
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                ).first()
                
                if session:
                    return session
            
            # Создаем новую сессию
            new_session = ChatSession(
                user_id=user_id,
                session_id=str(uuid.uuid4()),
                title="Новый диалог",
                model_used="gigachat"
            )
            
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            logger.info(f"Создана новая сессия: {new_session.session_id}")
            return new_session
            
        finally:
            db.close()
    
    async def _get_conversation_history(self, session_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """Получает историю диалога из БД"""
        db = next(get_db())
        
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(limit * 2).all()
            
            # Преобразуем в формат для LLM
            history = []
            for msg in reversed(messages):  # В хронологическом порядке
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            return history
            
        finally:
            db.close()
    
    async def _save_messages(self, session_id: int, user_message: str, response: Dict[str, Any]):
        """Сохраняет сообщения пользователя и ответ в БД"""
        db = next(get_db())
        
        try:
            # Сохраняем сообщение пользователя
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=user_message,
                created_at=datetime.now()
            )
            db.add(user_msg)
            
            # Сохраняем ответ ассистента
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response.get("content", ""),
                model_used=response.get("model_used"),
                tokens_used=response.get("tokens_used", 0),
                response_time=response.get("response_time", 0),
                context_sources=response.get("context_sources"),
                similarity_scores=response.get("similarity_scores"),
                created_at=datetime.now()
            )
            db.add(assistant_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщений: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def _update_session(self, session_id: int, model_used: str = None):
        """Обновляет информацию о сессии"""
        db = next(get_db())
        
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.now()
                if model_used:
                    session.model_used = model_used
                db.commit()
        finally:
            db.close()
    
    async def get_user_sessions(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список сессий пользователя"""
        db = next(get_db())
        
        try:
            sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
            
            result = []
            for session in sessions:
                # Получаем последнее сообщение для превью
                last_message = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).order_by(ChatMessage.created_at.desc()).first()
                
                result.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "model_used": session.model_used,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "last_message": last_message.content if last_message else "",
                    "message_count": db.query(ChatMessage).filter(
                        ChatMessage.session_id == session.id
                    ).count()
                })
            
            return result
            
        finally:
            db.close()
    
    async def get_session_messages(self, user_id: int, session_id: str, 
                                 limit: int = 50) -> List[Dict[str, Any]]:
        """Получает сообщения конкретной сессии"""
        db = next(get_db())
        
        try:
            # Проверяем права доступа
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                return []
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            result = []
            for msg in reversed(messages):  # В хронологическом порядке
                result.append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "model_used": msg.model_used,
                    "tokens_used": msg.tokens_used,
                    "response_time": msg.response_time,
                    "created_at": msg.created_at.isoformat(),
                    "context_sources": msg.context_sources,
                    "similarity_scores": msg.similarity_scores
                })
            
            return result
            
        finally:
            db.close()
    
    async def update_session_title(self, user_id: int, session_id: str, title: str) -> bool:
        """Обновляет заголовок сессии"""
        db = next(get_db())
        
        try:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if session:
                session.title = title
                session.updated_at = datetime.now()
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления заголовка сессии: {str(e)}")
            return False
        finally:
            db.close()
    
    async def delete_session(self, user_id: int, session_id: str) -> bool:
        """Удаляет сессию (помечает как неактивную)"""
        db = next(get_db())
        
        try:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if session:
                session.is_active = False
                session.updated_at = datetime.now()
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления сессии: {str(e)}")
            return False
        finally:
            db.close()


# Глобальный экземпляр сервиса
chat_service = ChatService()
