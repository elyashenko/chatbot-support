#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import create_tables, engine
from app.core.database import User, ChatSession, ChatMessage, Feedback, KnowledgeDocument, SystemMetrics
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib
from loguru import logger


def create_test_data():
    """Создает тестовые данные"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Создаем тестового пользователя
        test_user = db.query(User).filter(User.username == "test_user").first()
        if not test_user:
            test_user = User(
                username="test_user",
                email="test@example.com",
                hashed_password=hashlib.sha256("test_password".encode()).hexdigest(),
                role="developer",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            logger.info("Создан тестовый пользователь")
        
        # Создаем тестовую сессию
        test_session = db.query(ChatSession).filter(
            ChatSession.user_id == test_user.id,
            ChatSession.title == "Тестовая сессия"
        ).first()
        
        if not test_session:
            test_session = ChatSession(
                user_id=test_user.id,
                session_id="test-session-001",
                title="Тестовая сессия",
                model_used="gigachat",
                is_active=True
            )
            db.add(test_session)
            db.commit()
            db.refresh(test_session)
            logger.info("Создана тестовая сессия")
        
        # Создаем тестовые сообщения
        test_messages = [
            {
                "role": "user",
                "content": "Привет! Как настроить CI/CD пайплайн?",
                "model_used": None
            },
            {
                "role": "assistant", 
                "content": "Привет! Для настройки CI/CD пайплайна вам понадобится:\n\n1. **GitHub Actions** или **GitLab CI**\n2. **Docker** для контейнеризации\n3. **Kubernetes** для оркестрации\n\nХотите, чтобы я подробнее рассказал о каком-то из этих компонентов?",
                "model_used": "gigachat",
                "tokens_used": 150,
                "response_time": 2.5
            },
            {
                "role": "user",
                "content": "Расскажи про GitHub Actions",
                "model_used": None
            },
            {
                "role": "assistant",
                "content": "**GitHub Actions** - это система автоматизации CI/CD, встроенная в GitHub.\n\n## Основные компоненты:\n\n- **Workflows** - файлы YAML с описанием задач\n- **Jobs** - отдельные задачи\n- **Steps** - шаги внутри задач\n- **Actions** - переиспользуемые компоненты\n\n## Пример workflow:\n\n```yaml\nname: CI/CD Pipeline\non:\n  push:\n    branches: [main]\n\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v3\n    - name: Build\n      run: npm install && npm run build\n```",
                "model_used": "gigachat",
                "tokens_used": 200,
                "response_time": 3.1
            }
        ]
        
        for i, msg_data in enumerate(test_messages):
            existing_msg = db.query(ChatMessage).filter(
                ChatMessage.session_id == test_session.id,
                ChatMessage.content == msg_data["content"]
            ).first()
            
            if not existing_msg:
                message = ChatMessage(
                    session_id=test_session.id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    model_used=msg_data.get("model_used"),
                    tokens_used=msg_data.get("tokens_used"),
                    response_time=msg_data.get("response_time"),
                    created_at=datetime.now()
                )
                db.add(message)
                logger.info(f"Создано тестовое сообщение {i+1}")
        
        # Создаем тестовые документы знаний
        test_docs = [
            {
                "title": "CI/CD Основы",
                "content": "CI/CD (Continuous Integration/Continuous Deployment) - это практика автоматизации процессов разработки, тестирования и развертывания программного обеспечения.",
                "source_type": "manual",
                "source_url": "https://example.com/cicd-basics"
            },
            {
                "title": "Docker Контейнеризация",
                "content": "Docker позволяет упаковывать приложения в контейнеры, что обеспечивает консистентность между различными средами разработки и развертывания.",
                "source_type": "manual", 
                "source_url": "https://example.com/docker"
            }
        ]
        
        for doc_data in test_docs:
            existing_doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.title == doc_data["title"]
            ).first()
            
            if not existing_doc:
                doc = KnowledgeDocument(
                    title=doc_data["title"],
                    content=doc_data["content"],
                    source_type=doc_data["source_type"],
                    source_url=doc_data["source_url"],
                    is_active=True
                )
                db.add(doc)
                logger.info(f"Создан тестовый документ: {doc_data['title']}")
        
        db.commit()
        logger.info("Тестовые данные успешно созданы")
        
    except Exception as e:
        logger.error(f"Ошибка создания тестовых данных: {str(e)}")
        db.rollback()
    finally:
        db.close()


def main():
    """Основная функция"""
    logger.info("Начинаем инициализацию базы данных...")
    
    try:
        # Создаем таблицы
        create_tables()
        logger.info("Таблицы базы данных созданы")
        
        # Создаем тестовые данные
        create_test_data()
        
        logger.info("Инициализация базы данных завершена успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
