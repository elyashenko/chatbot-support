from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import os
from loguru import logger
from .core.config import settings
from .core.database import init_db, create_tables
from .api import chat, websocket

# Настройка логирования
logger.add(
    settings.log_file,
    rotation="10 MB",
    retention="7 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

# Создание FastAPI приложения
app = FastAPI(
    title="Chatbot Support API",
    description="RAG чат-бот поддержки для разработчиков",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"Входящий запрос: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Логируем время выполнения
    process_time = time.time() - start_time
    logger.info(f"Запрос обработан за {process_time:.3f}с: {response.status_code}")
    
    return response


# Middleware для обработки ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Глобальная ошибка: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )


# Подключаем роутеры
app.include_router(chat.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    logger.info("Запуск Chatbot Support API...")
    
    try:
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        create_tables()
        logger.info("База данных инициализирована")
        
        # Создаем директории для данных
        os.makedirs(settings.chroma_persist_directory, exist_ok=True)
        os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
        
        logger.info("Chatbot Support API успешно запущен")
        
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("Остановка Chatbot Support API...")


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Chatbot Support API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.get("/api/status")
async def api_status():
    """Статус API"""
    try:
        from .models.rag_engine import rag_pipeline
        
        return {
            "status": "running",
            "available_models": rag_pipeline.get_available_models(),
            "vector_store_stats": rag_pipeline.get_vector_store_stats(),
            "websocket_connections": len(websocket.manager.active_connections)
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса API: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# Подключаем статические файлы (если есть)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    logger.warning("Директория static не найдена")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
