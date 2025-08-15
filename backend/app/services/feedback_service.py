from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
from ..core.database import get_db, Feedback, ChatMessage, User


class FeedbackService:
    """Сервис для обработки обратной связи"""
    
    async def submit_feedback(self, user_id: int, message_id: int, 
                            rating: int, comment: str = None) -> Dict[str, Any]:
        """Отправляет обратную связь"""
        try:
            db = next(get_db())
            
            # Проверяем существование сообщения
            message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if not message:
                return {"success": False, "error": "Сообщение не найдено"}
            
            # Проверяем права доступа (пользователь может оценивать только свои сообщения)
            session = db.query(ChatMessage).filter(
                ChatMessage.id == message_id,
                ChatMessage.session_id == ChatMessage.session_id
            ).join(User).filter(User.id == user_id).first()
            
            if not session:
                return {"success": False, "error": "Нет прав для оценки этого сообщения"}
            
            # Создаем запись обратной связи
            feedback = Feedback(
                user_id=user_id,
                message_id=message_id,
                rating=rating,
                comment=comment,
                created_at=datetime.now()
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            logger.info(f"Получена обратная связь: пользователь {user_id}, сообщение {message_id}, оценка {rating}")
            
            return {
                "success": True,
                "feedback_id": feedback.id,
                "message": "Обратная связь успешно отправлена"
            }
            
        except Exception as e:
            logger.error(f"Ошибка отправки обратной связи: {str(e)}")
            return {"success": False, "error": "Ошибка отправки обратной связи"}
        finally:
            db.close()
    
    async def get_user_feedback(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает обратную связь пользователя"""
        try:
            db = next(get_db())
            
            feedbacks = db.query(Feedback).filter(
                Feedback.user_id == user_id
            ).order_by(Feedback.created_at.desc()).limit(limit).all()
            
            result = []
            for feedback in feedbacks:
                # Получаем информацию о сообщении
                message = db.query(ChatMessage).filter(
                    ChatMessage.id == feedback.message_id
                ).first()
                
                result.append({
                    "id": feedback.id,
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "created_at": feedback.created_at.isoformat(),
                    "message_content": message.content if message else "",
                    "message_role": message.role if message else "",
                    "model_used": message.model_used if message else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения обратной связи: {str(e)}")
            return []
        finally:
            db.close()
    
    async def get_system_feedback_stats(self) -> Dict[str, Any]:
        """Получает статистику обратной связи по системе"""
        try:
            db = next(get_db())
            
            # Общая статистика
            total_feedback = db.query(Feedback).count()
            
            if total_feedback == 0:
                return {
                    "total_feedback": 0,
                    "average_rating": 0,
                    "rating_distribution": {},
                    "recent_feedback": []
                }
            
            # Средняя оценка
            avg_rating = db.query(Feedback.rating).all()
            avg_rating = sum(r[0] for r in avg_rating) / len(avg_rating)
            
            # Распределение оценок
            rating_distribution = {}
            for i in range(1, 6):
                count = db.query(Feedback).filter(Feedback.rating == i).count()
                rating_distribution[str(i)] = count
            
            # Последние отзывы
            recent_feedback = db.query(Feedback).order_by(
                Feedback.created_at.desc()
            ).limit(10).all()
            
            recent_data = []
            for feedback in recent_feedback:
                message = db.query(ChatMessage).filter(
                    ChatMessage.id == feedback.message_id
                ).first()
                
                recent_data.append({
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "created_at": feedback.created_at.isoformat(),
                    "message_preview": message.content[:100] + "..." if message and len(message.content) > 100 else message.content if message else ""
                })
            
            return {
                "total_feedback": total_feedback,
                "average_rating": round(avg_rating, 2),
                "rating_distribution": rating_distribution,
                "recent_feedback": recent_data
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики обратной связи: {str(e)}")
            return {"error": str(e)}
        finally:
            db.close()
    
    async def get_model_performance_stats(self) -> Dict[str, Any]:
        """Получает статистику производительности моделей"""
        try:
            db = next(get_db())
            
            # Группируем по моделям
            model_stats = {}
            
            feedbacks = db.query(Feedback).join(ChatMessage).all()
            
            for feedback in feedbacks:
                model = feedback.message.model_used or "unknown"
                
                if model not in model_stats:
                    model_stats[model] = {
                        "total_feedback": 0,
                        "total_rating": 0,
                        "ratings": []
                    }
                
                model_stats[model]["total_feedback"] += 1
                model_stats[model]["total_rating"] += feedback.rating
                model_stats[model]["ratings"].append(feedback.rating)
            
            # Вычисляем средние оценки
            for model, stats in model_stats.items():
                stats["average_rating"] = round(
                    stats["total_rating"] / stats["total_feedback"], 2
                )
                del stats["total_rating"]
                del stats["ratings"]
            
            return model_stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики моделей: {str(e)}")
            return {"error": str(e)}
        finally:
            db.close()
    
    async def delete_feedback(self, user_id: int, feedback_id: int) -> Dict[str, Any]:
        """Удаляет обратную связь"""
        try:
            db = next(get_db())
            
            feedback = db.query(Feedback).filter(
                Feedback.id == feedback_id,
                Feedback.user_id == user_id
            ).first()
            
            if not feedback:
                return {"success": False, "error": "Обратная связь не найдена"}
            
            db.delete(feedback)
            db.commit()
            
            return {"success": True, "message": "Обратная связь удалена"}
            
        except Exception as e:
            logger.error(f"Ошибка удаления обратной связи: {str(e)}")
            return {"success": False, "error": "Ошибка удаления обратной связи"}
        finally:
            db.close()


# Глобальный экземпляр сервиса
feedback_service = FeedbackService()
