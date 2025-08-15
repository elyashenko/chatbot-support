from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from loguru import logger
from ..services.chat_service import chat_service
from ..core.database import get_db, User
from ..models.rag_engine import rag_pipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])
security = HTTPBearer()


# Pydantic модели для запросов и ответов
class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    preferred_model: Optional[str] = None


class ChatMessageResponse(BaseModel):
    session_id: str
    response: str
    model_used: str
    context_sources: List[Dict[str, Any]]
    similarity_scores: List[float]
    response_time: float
    success: bool


class SessionInfo(BaseModel):
    session_id: str
    title: str
    model_used: str
    created_at: str
    updated_at: str
    last_message: str
    message_count: int


class MessageInfo(BaseModel):
    id: int
    role: str
    content: str
    model_used: Optional[str]
    tokens_used: Optional[int]
    response_time: Optional[float]
    created_at: str
    context_sources: Optional[str]
    similarity_scores: Optional[str]


class UpdateSessionRequest(BaseModel):
    title: str


# Временная функция для получения пользователя (в реальном приложении - JWT токен)
async def get_current_user(token: str = Depends(security)) -> User:
    """Получает текущего пользователя из токена"""
    # TODO: Реализовать JWT аутентификацию
    # Пока возвращаем тестового пользователя
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            # Создаем тестового пользователя
            user = User(
                username="test_user",
                email="test@example.com",
                hashed_password="hashed_password",
                role="developer"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """Отправляет сообщение и получает ответ от чат-бота"""
    try:
        logger.info(f"Получен запрос от пользователя {current_user.id}: {request.message[:100]}...")
        
        response = await chat_service.process_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            preferred_model=request.preferred_model
        )
        
        if not response.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.get("error", "Ошибка обработки сообщения")
            )
        
        return ChatMessageResponse(
            session_id=response["session_id"],
            response=response["response"],
            model_used=response["model_used"],
            context_sources=response["context_sources"],
            similarity_scores=response["similarity_scores"],
            response_time=response["response_time"],
            success=response["success"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Получает список сессий пользователя"""
    try:
        sessions = await chat_service.get_user_sessions(
            user_id=current_user.id,
            limit=limit
        )
        
        return [SessionInfo(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Ошибка получения сессий: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка сессий"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageInfo])
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Получает сообщения конкретной сессии"""
    try:
        messages = await chat_service.get_session_messages(
            user_id=current_user.id,
            session_id=session_id,
            limit=limit
        )
        
        return [MessageInfo(**message) for message in messages]
        
    except Exception as e:
        logger.error(f"Ошибка получения сообщений сессии: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения сообщений"
        )


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Обновляет заголовок сессии"""
    try:
        success = await chat_service.update_session_title(
            user_id=current_user.id,
            session_id=session_id,
            title=request.title
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия не найдена"
            )
        
        return {"message": "Заголовок сессии обновлен"}
        
    except Exception as e:
        logger.error(f"Ошибка обновления заголовка сессии: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления заголовка"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Удаляет сессию"""
    try:
        success = await chat_service.delete_session(
            user_id=current_user.id,
            session_id=session_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия не найдена"
            )
        
        return {"message": "Сессия удалена"}
        
    except Exception as e:
        logger.error(f"Ошибка удаления сессии: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления сессии"
        )


@router.get("/models")
async def get_available_models():
    """Получает список доступных AI моделей"""
    try:
        models = rag_pipeline.get_available_models()
        return {
            "available_models": models,
            "default_model": "gigachat",
            "fallback_models": ["deepseek", "openai"]
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка моделей"
        )


@router.get("/stats")
async def get_system_stats():
    """Получает статистику системы"""
    try:
        vector_stats = rag_pipeline.get_vector_store_stats()
        return {
            "vector_store": vector_stats,
            "available_models": rag_pipeline.get_available_models()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики"
        )


@router.post("/test")
async def test_chat():
    """Тестовый endpoint для проверки работы чат-бота"""
    try:
        # Создаем тестового пользователя
        db = next(get_db())
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(
                username="test_user",
                email="test@example.com",
                hashed_password="hashed_password",
                role="developer"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        db.close()
        
        # Тестовый запрос
        response = await chat_service.process_message(
            user_id=user.id,
            message="Привет! Как дела?",
            preferred_model="gigachat"
        )
        
        return {
            "message": "Тест успешен",
            "response": response,
            "user_id": user.id
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка тестирования: {str(e)}"
        )
