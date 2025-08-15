# API Документация

## Обзор

Chatbot Support API предоставляет REST и WebSocket endpoints для работы с RAG чат-ботом поддержки разработчиков.

## Базовый URL

```
http://localhost:8000
```

## Аутентификация

В текущей версии используется временная аутентификация с Bearer токеном:

```
Authorization: Bearer test-token
```

## REST API Endpoints

### Чат

#### POST /api/chat/message

Отправляет сообщение и получает ответ от чат-бота.

**Запрос:**
```json
{
  "message": "Как настроить CI/CD пайплайн?",
  "session_id": "optional-session-id",
  "preferred_model": "gigachat"
}
```

**Ответ:**
```json
{
  "session_id": "uuid-session-id",
  "response": "Для настройки CI/CD пайплайна...",
  "model_used": "gigachat",
  "context_sources": [
    {
      "id": "doc-1",
      "title": "CI/CD Основы",
      "url": "https://example.com/cicd-basics",
      "similarity": 0.85
    }
  ],
  "similarity_scores": [0.85, 0.72, 0.65],
  "response_time": 2.5,
  "success": true
}
```

#### GET /api/chat/sessions

Получает список сессий пользователя.

**Параметры:**
- `limit` (int, optional): Количество сессий (по умолчанию 20)

**Ответ:**
```json
[
  {
    "session_id": "uuid-session-id",
    "title": "Новый диалог",
    "model_used": "gigachat",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:30:00Z",
    "last_message": "Как настроить CI/CD?",
    "message_count": 5
  }
]
```

#### GET /api/chat/sessions/{session_id}/messages

Получает сообщения конкретной сессии.

**Параметры:**
- `limit` (int, optional): Количество сообщений (по умолчанию 50)

**Ответ:**
```json
[
  {
    "id": 1,
    "role": "user",
    "content": "Привет!",
    "model_used": null,
    "tokens_used": null,
    "response_time": null,
    "created_at": "2024-01-01T12:00:00Z",
    "context_sources": null,
    "similarity_scores": null
  }
]
```

#### PUT /api/chat/sessions/{session_id}/title

Обновляет заголовок сессии.

**Запрос:**
```json
{
  "title": "Новый заголовок"
}
```

#### DELETE /api/chat/sessions/{session_id}

Удаляет сессию.

#### GET /api/chat/models

Получает список доступных AI моделей.

**Ответ:**
```json
{
  "available_models": ["gigachat", "deepseek", "openai"],
  "default_model": "gigachat",
  "fallback_models": ["deepseek", "openai"]
}
```

#### GET /api/chat/stats

Получает статистику системы.

**Ответ:**
```json
{
  "vector_store": {
    "total_documents": 150,
    "collection_name": "knowledge_base",
    "persist_directory": "./data/chroma_db"
  },
  "available_models": ["gigachat", "deepseek", "openai"]
}
```

### Системные Endpoints

#### GET /

Корневой endpoint.

**Ответ:**
```json
{
  "message": "Chatbot Support API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

#### GET /health

Health check endpoint.

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": 1704067200.0,
  "version": "1.0.0"
}
```

#### GET /api/status

Статус API с детальной информацией.

**Ответ:**
```json
{
  "status": "running",
  "available_models": ["gigachat", "deepseek", "openai"],
  "vector_store_stats": {
    "total_documents": 150,
    "collection_name": "knowledge_base",
    "persist_directory": "./data/chroma_db"
  },
  "websocket_connections": 5
}
```

## WebSocket API

### Подключение

```
ws://localhost:8000/ws/{user_id}
```

### Отправка сообщений

#### Чат-сообщение
```json
{
  "type": "chat",
  "message": "Как настроить CI/CD?",
  "session_id": "optional-session-id",
  "preferred_model": "gigachat"
}
```

#### Индикатор печати
```json
{
  "type": "typing",
  "status": "start"
}
```

#### Запрос сессий
```json
{
  "type": "session",
  "action": "get_sessions"
}
```

#### Запрос сообщений сессии
```json
{
  "type": "session",
  "action": "get_messages",
  "session_id": "uuid-session-id"
}
```

#### Обновление заголовка сессии
```json
{
  "type": "session",
  "action": "update_title",
  "session_id": "uuid-session-id",
  "title": "Новый заголовок"
}
```

#### Удаление сессии
```json
{
  "type": "session",
  "action": "delete_session",
  "session_id": "uuid-session-id"
}
```

### Получение сообщений

#### Подключение
```json
{
  "type": "connection",
  "message": "Подключение установлено",
  "user_id": "1",
  "timestamp": 1704067200.0
}
```

#### Ответ чата
```json
{
  "type": "chat_response",
  "session_id": "uuid-session-id",
  "response": "Для настройки CI/CD...",
  "model_used": "gigachat",
  "context_sources": [...],
  "similarity_scores": [0.85, 0.72],
  "response_time": 2.5,
  "success": true,
  "timestamp": 1704067200.0
}
```

#### Индикатор печати
```json
{
  "type": "typing",
  "status": "start",
  "timestamp": 1704067200.0
}
```

#### Список сессий
```json
{
  "type": "sessions_list",
  "sessions": [...],
  "timestamp": 1704067200.0
}
```

#### Список сообщений
```json
{
  "type": "messages_list",
  "session_id": "uuid-session-id",
  "messages": [...],
  "timestamp": 1704067200.0
}
```

#### Ошибка
```json
{
  "type": "error",
  "message": "Описание ошибки",
  "timestamp": 1704067200.0
}
```

## Коды ошибок

- `400` - Неверный запрос
- `401` - Не авторизован
- `404` - Не найдено
- `500` - Внутренняя ошибка сервера

## Ограничения

- Максимальная длина сообщения: 2000 символов
- Максимальное количество сообщений в сессии: 50
- Таймаут запроса: 30 секунд
- Rate limiting: 60 запросов в минуту, 1000 в час

## Примеры использования

### JavaScript (Fetch API)

```javascript
// Отправка сообщения
const response = await fetch('/api/chat/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer test-token'
  },
  body: JSON.stringify({
    message: 'Как настроить CI/CD?',
    preferred_model: 'gigachat'
  })
});

const data = await response.json();
console.log(data.response);
```

### JavaScript (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/1');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Отправка сообщения
ws.send(JSON.stringify({
  type: 'chat',
  message: 'Как настроить CI/CD?'
}));
```

### Python (requests)

```python
import requests

# Отправка сообщения
response = requests.post(
    'http://localhost:8000/api/chat/message',
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
    },
    json={
        'message': 'Как настроить CI/CD?',
        'preferred_model': 'gigachat'
    }
)

data = response.json()
print(data['response'])
```
