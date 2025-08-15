# Chatbot Support - RAG чат-бот поддержки разработчиков

Production-ready чат-бот поддержки для разработчиков на базе RAG и векторного поиска. Проект закрывает 30% обращений в техподдержку и сокращает время решения с 2 часов до 15 минут.

## Технический стек

**Backend:**
- Python (FastAPI)
- Векторная БД: Chroma
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

## Быстрый старт

### Локальная разработка

1. Клонируйте репозиторий
2. Установите зависимости:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

3. Настройте переменные окружения:
   ```bash
   cp backend/.env.example backend/.env
   # Отредактируйте .env файл с вашими API ключами
   ```

4. Запустите с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Production развертывание

См. `docs/deployment.md` для подробных инструкций.

## Основной функционал

- Ответы на вопросы по CI/CD процессам
- Поиск по документации разработчика
- История чатов пользователя
- Система feedback и оценок
- Многопользовательский режим
- Real-time чат через WebSocket

## API документация

После запуска доступна по адресу: http://localhost:8000/docs

## Лицензия

MIT
