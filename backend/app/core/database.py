from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from .config import settings

# Создание движка базы данных
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="developer")  # developer, admin, support
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    chat_sessions = relationship("ChatSession", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200))
    model_used = Column(String(50))  # gigachat, deepseek, openai
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Связи
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    response_time = Column(Float)  # время ответа в секундах
    created_at = Column(DateTime, default=func.now())
    
    # RAG контекст
    context_sources = Column(Text)  # JSON с источниками контекста
    similarity_scores = Column(Text)  # JSON с оценками схожести
    
    # Связи
    session = relationship("ChatSession", back_populates="messages")


class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 звезд
    comment = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Связи
    user = relationship("User", back_populates="feedback")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String(50))  # confluence, manual, faq
    source_url = Column(String(500))
    space_key = Column(String(50))  # для Confluence
    page_id = Column(String(100))  # для Confluence
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    timestamp = Column(DateTime, default=func.now())
    model_used = Column(String(50))
    session_id = Column(String(100))


# Функции для работы с базой данных
def get_db():
    """Генератор сессий базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)


def create_tables():
    """Создание всех таблиц"""
    Base.metadata.create_all(bind=engine)
