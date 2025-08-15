from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer
from typing import Dict, List, Any
import json
import asyncio
from loguru import logger
from ..services.chat_service import chat_service
from ..core.database import get_db, User

router = APIRouter()
security = HTTPBearer()


class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Подключает пользователя к WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"Пользователь {user_id} подключен к WebSocket")
    
    def disconnect(self, user_id: str):
        """Отключает пользователя от WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"Пользователь {user_id} отключен от WebSocket")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        """Отправляет личное сообщение пользователю"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {str(e)}")
                self.disconnect(user_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Отправляет сообщение всем подключенным пользователям"""
        disconnected_users = []
        
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Ошибка отправки broadcast сообщения пользователю {user_id}: {str(e)}")
                disconnected_users.append(user_id)
        
        # Удаляем отключенных пользователей
        for user_id in disconnected_users:
            self.disconnect(user_id)


# Глобальный менеджер соединений
manager = ConnectionManager()


# Временная функция для получения пользователя из WebSocket
async def get_user_from_websocket(websocket: WebSocket) -> User:
    """Получает пользователя из WebSocket соединения"""
    # В реальном приложении здесь должна быть JWT аутентификация
    # Пока возвращаем тестового пользователя
    db = next(get_db())
    try:
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
        return user
    finally:
        db.close()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint для real-time чата"""
    await manager.connect(websocket, user_id)
    
    try:
        # Получаем пользователя
        user = await get_user_from_websocket(websocket)
        
        # Отправляем приветственное сообщение
        await manager.send_personal_message({
            "type": "connection",
            "message": "Подключение установлено",
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)
        
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Обрабатываем сообщение
            await process_websocket_message(user, message_data, user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Ошибка WebSocket соединения для пользователя {user_id}: {str(e)}")
        manager.disconnect(user_id)


async def process_websocket_message(user: User, message_data: Dict[str, Any], user_id: str):
    """Обрабатывает сообщение от WebSocket клиента"""
    try:
        message_type = message_data.get("type", "chat")
        
        if message_type == "chat":
            await handle_chat_message(user, message_data, user_id)
        elif message_type == "typing":
            await handle_typing_indicator(user, message_data, user_id)
        elif message_type == "session":
            await handle_session_message(user, message_data, user_id)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": f"Неизвестный тип сообщения: {message_type}",
                "timestamp": asyncio.get_event_loop().time()
            }, user_id)
            
    except Exception as e:
        logger.error(f"Ошибка обработки WebSocket сообщения: {str(e)}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Ошибка обработки сообщения",
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)


async def handle_chat_message(user: User, message_data: Dict[str, Any], user_id: str):
    """Обрабатывает чат-сообщение"""
    try:
        message = message_data.get("message", "")
        session_id = message_data.get("session_id")
        preferred_model = message_data.get("preferred_model")
        
        if not message:
            await manager.send_personal_message({
                "type": "error",
                "message": "Пустое сообщение",
                "timestamp": asyncio.get_event_loop().time()
            }, user_id)
            return
        
        # Отправляем индикатор "печатает"
        await manager.send_personal_message({
            "type": "typing",
            "status": "start",
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)
        
        # Обрабатываем сообщение через RAG
        response = await chat_service.process_message(
            user_id=user.id,
            message=message,
            session_id=session_id,
            preferred_model=preferred_model
        )
        
        # Останавливаем индикатор "печатает"
        await manager.send_personal_message({
            "type": "typing",
            "status": "stop",
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)
        
        # Отправляем ответ
        await manager.send_personal_message({
            "type": "chat_response",
            "session_id": response.get("session_id"),
            "response": response.get("response"),
            "model_used": response.get("model_used"),
            "context_sources": response.get("context_sources", []),
            "similarity_scores": response.get("similarity_scores", []),
            "response_time": response.get("response_time", 0),
            "success": response.get("success", False),
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)
        
        # Обновляем сессию пользователя
        if response.get("session_id"):
            manager.user_sessions[user_id] = response["session_id"]
        
    except Exception as e:
        logger.error(f"Ошибка обработки чат-сообщения: {str(e)}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Ошибка обработки сообщения",
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)


async def handle_typing_indicator(user: User, message_data: Dict[str, Any], user_id: str):
    """Обрабатывает индикатор печати"""
    try:
        status = message_data.get("status", "start")
        
        # В реальном приложении здесь можно уведомить других пользователей
        # о том, что пользователь печатает
        
        await manager.send_personal_message({
            "type": "typing_ack",
            "status": status,
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)
        
    except Exception as e:
        logger.error(f"Ошибка обработки индикатора печати: {str(e)}")


async def handle_session_message(user: User, message_data: Dict[str, Any], user_id: str):
    """Обрабатывает сообщения, связанные с сессиями"""
    try:
        action = message_data.get("action")
        
        if action == "get_sessions":
            sessions = await chat_service.get_user_sessions(user_id=user.id)
            await manager.send_personal_message({
                "type": "sessions_list",
                "sessions": sessions,
                "timestamp": asyncio.get_event_loop().time()
            }, user_id)
            
        elif action == "get_messages":
            session_id = message_data.get("session_id")
            if session_id:
                messages = await chat_service.get_session_messages(
                    user_id=user.id,
                    session_id=session_id
                )
                await manager.send_personal_message({
                    "type": "messages_list",
                    "session_id": session_id,
                    "messages": messages,
                    "timestamp": asyncio.get_event_loop().time()
                }, user_id)
        
        elif action == "update_title":
            session_id = message_data.get("session_id")
            title = message_data.get("title")
            if session_id and title:
                success = await chat_service.update_session_title(
                    user_id=user.id,
                    session_id=session_id,
                    title=title
                )
                await manager.send_personal_message({
                    "type": "title_updated",
                    "session_id": session_id,
                    "success": success,
                    "timestamp": asyncio.get_event_loop().time()
                }, user_id)
        
        elif action == "delete_session":
            session_id = message_data.get("session_id")
            if session_id:
                success = await chat_service.delete_session(
                    user_id=user.id,
                    session_id=session_id
                )
                await manager.send_personal_message({
                    "type": "session_deleted",
                    "session_id": session_id,
                    "success": success,
                    "timestamp": asyncio.get_event_loop().time()
                }, user_id)
        
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": f"Неизвестное действие: {action}",
                "timestamp": asyncio.get_event_loop().time()
            }, user_id)
            
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения сессии: {str(e)}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Ошибка обработки запроса сессии",
            "timestamp": asyncio.get_event_loop().time()
        }, user_id)


@router.get("/ws/status")
async def get_websocket_status():
    """Получает статус WebSocket соединений"""
    return {
        "active_connections": len(manager.active_connections),
        "connected_users": list(manager.active_connections.keys()),
        "user_sessions": manager.user_sessions
    }
