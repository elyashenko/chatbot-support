# Источники данных для векторной базы

## 📚 Откуда взять документы для RAG системы

### 1. **Confluence (основной источник)**

#### Что это такое
Confluence - это корпоративная платформа для совместной работы над документацией от Atlassian. Идеально подходит для технической документации, API docs, руководств пользователей.

#### Что можно получить
- **Техническая документация**: API endpoints, схемы, примеры
- **Руководства пользователей**: инструкции, туториалы, FAQ
- **Процессы и процедуры**: workflow, best practices
- **Архитектурные решения**: ADR (Architecture Decision Records)
- **Спецификации**: требования, дизайн-документы

#### Как настроить интеграцию
```env
# В .env файле
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your_email@example.com
CONFLUENCE_API_TOKEN=your_api_token
CONFLUENCE_SPACE_KEYS=["SPACE1", "SPACE2"]
```

#### Процесс синхронизации
1. **Автоматическая**: Каждые 6 часов
2. **Ручная**: По требованию через API
3. **Инкрементальная**: Только измененные страницы

#### Примеры контента
```
📄 API Documentation
├── Authentication
├── Endpoints
│   ├── GET /users
│   ├── POST /users
│   └── PUT /users/{id}
└── Error Codes

📄 User Guides
├── Getting Started
├── Common Tasks
└── Troubleshooting

📄 Architecture
├── System Overview
├── Data Flow
└── Deployment
```

### 2. **GitHub/GitLab Repositories**

#### Markdown файлы
- `README.md` - описание проекта
- `docs/` - документация
- `CONTRIBUTING.md` - руководство для контрибьюторов
- `CHANGELOG.md` - история изменений

#### Пример структуры
```
project/
├── README.md
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   ├── api.md
│   └── troubleshooting.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

#### Автоматическая синхронизация
```python
# GitHub API integration
github_token = "your_github_token"
repo_owner = "your_username"
repo_name = "your_repo"

# Получение всех markdown файлов
markdown_files = get_markdown_files(github_token, repo_owner, repo_name)
```

### 3. **Технические блоги и статьи**

#### Внутренние блоги
- Medium, Dev.to, Hashnode
- Корпоративные блоги
- Технические новости

#### Внешние источники
- Stack Overflow (Q&A)
- Reddit (r/programming, r/webdev)
- Hacker News
- TechCrunch, The Verge

#### Примеры тем
```
🔧 Development
├── Best Practices
├── Code Reviews
├── Testing Strategies
└── Performance Optimization

🚀 DevOps
├── CI/CD Pipelines
├── Containerization
├── Monitoring
└── Security

💡 Problem Solving
├── Common Issues
├── Debugging Techniques
├── Performance Bottlenecks
└── Scalability Solutions
```

### 4. **Базы знаний и FAQ**

#### Структурированные FAQ
```
Q: Как настроить SSL сертификат?
A: 1. Получите сертификат от Let's Encrypt
    2. Установите в nginx
    3. Настройте auto-renewal

Q: Как оптимизировать запросы к базе данных?
A: 1. Добавьте индексы
    2. Используйте EXPLAIN
    3. Оптимизируйте JOIN'ы
```

#### Базы знаний
- **Notion** - структурированная документация
- **Airtable** - базы данных с API
- **Google Docs** - через Google Drive API
- **Microsoft SharePoint** - корпоративная документация

### 5. **API документация**

#### OpenAPI/Swagger
```yaml
openapi: 3.0.0
info:
  title: User Management API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get all users
      responses:
        '200':
          description: List of users
```

#### Postman Collections
- Экспорт в JSON
- Автоматическое извлечение описаний
- Примеры запросов и ответов

#### GraphQL Schema
```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
}
```

### 6. **Видео и аудио контент**

#### Транскрипции
- YouTube видео → автоматическая транскрипция
- Подкасты → расшифровка аудио
- Вебинары → записи и слайды

#### Инструменты
- **Whisper** (OpenAI) - транскрипция аудио
- **AssemblyAI** - профессиональная транскрипция
- **Rev.com** - ручная транскрипция

### 7. **Структурированные данные**

#### CSV/Excel файлы
```
Issue,Solution,Category,Priority
"SSL Error","Check certificate validity",Security,High
"Slow Queries","Add database indexes",Performance,Medium
"Login Failed","Verify credentials",Authentication,High
```

#### JSON/XML данные
```json
{
  "troubleshooting": {
    "common_issues": [
      {
        "title": "Database Connection Failed",
        "description": "Unable to connect to PostgreSQL",
        "solution": "Check connection string and credentials",
        "category": "Database"
      }
    ]
  }
}
```

## 🛠️ Инструменты для извлечения данных

### 1. **Web Scraping**
```python
import requests
from bs4 import BeautifulSoup
import trafilatura

def extract_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Извлечение основного контента
    content = trafilatura.extract(response.content)
    return content
```

### 2. **PDF Processing**
```python
import PyPDF2
import pdfplumber

def extract_pdf_text(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text
```

### 3. **Office Documents**
```python
from docx import Document
import openpyxl

def extract_docx_text(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text
```

## 📊 Стратегии сбора данных

### 1. **Приоритизация источников**
```
🔥 Высокий приоритет
├── Confluence (основная документация)
├── GitHub README и docs
├── API документация
└── FAQ и базы знаний

⚡ Средний приоритет
├── Технические блоги
├── Stack Overflow
├── Видео транскрипции
└── Структурированные данные

📚 Низкий приоритет
├── Внешние статьи
├── Социальные сети
├── Общие новости
└── Исторические данные
```

### 2. **Частота обновления**
- **Ежедневно**: FAQ, базы знаний
- **Еженедельно**: API docs, технические статьи
- **Ежемесячно**: Архитектурная документация
- **По требованию**: Критические обновления

### 3. **Качество данных**
```
✅ Хорошо
├── Актуальная информация
├── Структурированный контент
├── Проверенные источники
└── Регулярные обновления

⚠️ Требует проверки
├── Устаревшая информация
├── Неструктурированный контент
├── Непроверенные источники
└── Редкие обновления

❌ Исключить
├── Спам и реклама
├── Неактуальный контент
├── Дублирующаяся информация
└── Низкое качество
```

## 🔄 Процесс индексации

### 1. **Извлечение контента**
```python
def extract_content_from_source(source_type, source_url):
    if source_type == "confluence":
        return extract_confluence_content(source_url)
    elif source_type == "github":
        return extract_github_content(source_url)
    elif source_type == "web":
        return extract_web_content(source_url)
    elif source_type == "file":
        return extract_file_content(source_url)
```

### 2. **Предобработка**
```python
def preprocess_content(content):
    # Очистка HTML тегов
    content = clean_html(content)
    
    # Нормализация текста
    content = normalize_text(content)
    
    # Удаление дубликатов
    content = remove_duplicates(content)
    
    # Структурирование
    content = structure_content(content)
    
    return content
```

### 3. **Чанкирование**
```python
def chunk_content(content, chunk_size=1000, overlap=200):
    chunks = []
    
    # Разбиение по предложениям
    sentences = split_into_sentences(content)
    
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    return chunks
```

### 4. **Векторизация и сохранение**
```python
def index_content(chunks):
    for i, chunk in enumerate(chunks):
        # Векторизация
        embedding = embedding_model.encode(chunk)
        
        # Сохранение в ChromaDB
        vector_store.add(
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{
                "source": "confluence",
                "chunk_id": i,
                "timestamp": datetime.now()
            }]
        )
```

## 📈 Метрики качества данных

### 1. **Количественные метрики**
- **Объем данных**: Количество документов, чанков
- **Покрытие**: Процент вопросов с ответами
- **Актуальность**: Время с последнего обновления
- **Разнообразие**: Количество уникальных источников

### 2. **Качественные метрики**
- **Релевантность**: Соответствие контента вопросам
- **Точность**: Корректность информации
- **Полнота**: Достаточность деталей
- **Структурированность**: Организация контента

### 3. **Пользовательские метрики**
- **Feedback score**: Оценки ответов
- **Resolution rate**: Процент решенных проблем
- **User satisfaction**: Удовлетворенность пользователей
- **Time to resolution**: Время решения проблемы

## 🚀 Автоматизация процесса

### 1. **Scheduled Jobs**
```python
# Cron jobs для автоматической синхронизации
@cron("0 */6 * * *")  # Каждые 6 часов
def sync_confluence():
    sync_confluence_content()

@cron("0 0 * * 0")    # Еженедельно
def sync_github():
    sync_github_content()

@cron("0 2 * * *")    # Ежедневно в 2:00
def sync_web_sources():
    sync_web_content()
```

### 2. **Webhooks**
```python
@app.post("/webhook/confluence")
async def confluence_webhook(payload: dict):
    # Автоматическое обновление при изменении в Confluence
    page_id = payload["page_id"]
    update_confluence_page(page_id)
```

### 3. **Monitoring**
```python
def monitor_data_quality():
    # Проверка качества данных
    quality_score = calculate_quality_score()
    
    if quality_score < 0.7:
        send_alert("Data quality below threshold")
    
    # Проверка актуальности
    freshness_score = calculate_freshness_score()
    
    if freshness_score < 0.8:
        send_alert("Data may be outdated")
```

## 💡 Рекомендации по началу

### 1. **Начните с малого**
- 10-20 основных документов
- Простые FAQ
- Базовые инструкции

### 2. **Постепенно расширяйте**
- Добавляйте новые источники
- Улучшайте качество существующих
- Оптимизируйте процесс

### 3. **Измеряйте результаты**
- Отслеживайте метрики
- Собирайте обратную связь
- Адаптируйте стратегию

### 4. **Автоматизируйте**
- Настройте регулярную синхронизацию
- Используйте webhooks
- Мониторьте качество данных
