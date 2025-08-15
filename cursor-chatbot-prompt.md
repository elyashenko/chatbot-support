# Промпт для Cursor: RAG чат-бот поддержки разработчиков

Создай production-ready чат-бот поддержки для разработчиков на базе RAG и векторного поиска. Проект должен закрывать 30% обращений в техподдержку и сокращать время решения с 2 часов до 15 минут.

## Технический стек

**Backend:**
- Python (FastAPI)
- Векторная БД: Chroma/Pinecone
- AI модели: GigaChat API, DeepSeek API, OpenAI
- RAG pipeline с embeddings
- PostgreSQL для сессий и истории
- Confluence API интеграция
- WebSocket для real-time чата

**Frontend:**
- React + TypeScript
- WebSocket клиент
- Современный UI в корпоративном стиле
- История диалогов и feedback система

**DevOps:**
- Docker контейнеризация
- Docker Compose для локальной разработки
- Готовность к Kubernetes deployment
- CI/CD pipeline конфигурация

## Структура проекта

```
chatbot-support/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Конфигурация AI моделей
│   │   │   ├── llm_providers.py   # GigaChat, DeepSeek, OpenAI
│   │   │   └── database.py        # PostgreSQL подключение
│   │   ├── models/
│   │   │   ├── rag_engine.py      # RAG pipeline
│   │   │   ├── vector_store.py    # Векторные операции
│   │   │   └── embeddings.py      # Embedding модели
│   │   ├── services/
│   │   │   ├── confluence_sync.py # Синхронизация документации
│   │   │   ├── chat_service.py    # Обработка запросов
│   │   │   └── feedback_service.py # Сбор обратной связи
│   │   ├── api/
│   │   │   ├── chat.py            # REST endpoints
│   │   │   └── websocket.py       # WebSocket handlers
│   │   └── utils/
│   │       ├── preprocessing.py   # Обработка документов
│   │       └── metrics.py         # Мониторинг качества
│   ├── data/
│   │   ├── knowledge_base/        # Документация и FAQ
│   │   └── training_data/         # Примеры диалогов
│   ├── scripts/
│   │   ├── setup_db.py           # Инициализация БД
│   │   └── sync_confluence.py     # Загрузка документов
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/             # Компоненты чата
│   │   │   ├── History/          # История диалогов
│   │   │   └── Feedback/         # Система оценок
│   │   ├── services/
│   │   │   ├── api.ts            # HTTP клиент
│   │   │   └── websocket.ts      # WebSocket клиент
│   │   ├── hooks/
│   │   │   └── useChat.ts        # React hooks для чата
│   │   └── types/
│   │       └── chat.types.ts     # TypeScript типы
│   ├── package.json
│   └── tsconfig.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
└── docs/
    ├── api.md                    # API документация
    └── deployment.md             # Инструкции по развертыванию
```

## Ключевые компоненты для реализации

### 1. Multi-LLM Provider System
Создай универсальный интерфейс для работы с разными AI моделями:
- GigaChat API интеграция
- DeepSeek API поддержка  
- OpenAI как fallback
- Автоматическое переключение при недоступности
- Rate limiting и retry логика

### 2. RAG Pipeline
- Загрузка документов из Confluence API
- Chunking стратегии для разных типов документов
- Векторные embeddings (multilingual поддержка)
- Hybrid search (векторный + keyword)
- Context ranking и фильтрация

### 3. Чат-интерфейс
- Real-time сообщения через WebSocket
- История диалогов с контекстом
- Предложения популярных вопросов
- Markdown рендеринг ответов
- Копирование кода и команд
- Система лайков/дизлайков для обучения

### 4. Мониторинг и аналитика
- Логирование всех запросов и ответов
- Метрики качества (response time, user satisfaction)
- A/B тестирование разных промптов
- Dashboard для анализа эффективности

## Основной функционал

**MVP фичи:**
- Ответы на вопросы по CI/CD процессам
- Поиск по документации разработчика
- История чатов пользователя
- Базовая система feedback
- Многопользовательский режим

**Advanced фичи:**
- Контекстное понимание в рамках сессии  
- Персонализация под роль (Frontend/Backend/DevOps)
- Интеграция с корпоративными системами
- Автоматическое обновление базы знаний
- Уведомления о критических вопросах

## Конфигурация AI моделей

Предусмотри настройки для:
- GigaChat: температура, max_tokens, system prompts
- DeepSeek: специфические параметры модели
- Fallback цепочка: GigaChat → DeepSeek → OpenAI
- Кэширование ответов для оптимизации

## Требования к качеству

- Время ответа < 3 секунд
- Поддержка 100+ одновременных пользователей
- 95% uptime
- Корректные ответы на 80% типовых вопросов
- Русский и английский языки

Начни с создания базовой архитектуры и настройки multi-LLM provider system, затем добавь RAG pipeline и чат-интерфейс. Фокусируйся на production-ready коде с proper error handling и logging.