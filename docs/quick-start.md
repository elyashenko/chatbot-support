# 🚀 Быстрый старт с RAG Chatbot Support System

## ⚡ За 15 минут от нуля до работающей системы

### Шаг 1: Подготовка окружения (2 мин)

#### Проверьте Docker
```bash
docker --version
docker-compose --version
```

#### Клонируйте репозиторий
```bash
git clone https://github.com/elyashenko/chatbot-support.git
cd chatbot-support
```

### Шаг 2: Настройка конфигурации (3 мин)

#### Создайте .env файл
```bash
cp backend/env.example backend/.env
```

#### Отредактируйте .env
```env
# Обязательные настройки для начала
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_support
SECRET_KEY=your-secret-key-here-change-in-production

# Опционально - API ключи для LLM
GIGACHAT_API_KEY=your_gigachat_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Шаг 3: Запуск системы (5 мин)

#### Запустите базу данных
```bash
docker-compose up postgres redis -d
```

#### Запустите backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### В новом терминале запустите frontend
```bash
cd frontend
npm install
npm start
```

### Шаг 4: Проверка работы (3 мин)

#### Тест API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/chat/models
```

#### Откройте в браузере
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Шаг 5: Добавление первых документов (2 мин)

#### Создайте тестовые документы
```bash
cd backend
python scripts/setup_db.py
```

## 📚 Добавление документов в векторную базу

### Вариант 1: Быстрый старт с тестовыми данными

#### Создайте файл `test_docs.md`
```markdown
# Как настроить SSL сертификат

## Шаг 1: Получение сертификата
1. Установите certbot: `sudo apt install certbot`
2. Получите сертификат: `sudo certbot certonly --standalone -d yourdomain.com`

## Шаг 2: Настройка nginx
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
}
```

## Шаг 3: Автообновление
Добавьте в crontab: `0 12 * * * /usr/bin/certbot renew --quiet`
```

#### Загрузите в систему
```python
from app.models.vector_store import VectorStore
from app.models.embeddings import DocumentChunker

# Инициализация
vector_store = VectorStore()
chunker = DocumentChunker()

# Чанкирование документа
chunks = chunker.chunk_document(test_docs_content)

# Добавление в векторную базу
for chunk in chunks:
    vector_store.add_document(chunk, metadata={"source": "test_docs.md"})
```

### Вариант 2: Интеграция с Confluence

#### Настройте Confluence API
```env
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your_email@example.com
CONFLUENCE_API_TOKEN=your_api_token
CONFLUENCE_SPACE_KEYS=["SPACE1", "SPACE2"]
```

#### Запустите синхронизацию
```python
from app.services.confluence_sync import ConfluenceSync

sync = ConfluenceSync()
sync.sync_all_spaces()
```

### Вариант 3: Загрузка из GitHub

#### Создайте GitHub токен
1. Перейдите в Settings → Developer settings → Personal access tokens
2. Создайте токен с правами `repo` и `read:packages`

#### Настройте синхронизацию
```python
from app.services.github_sync import GitHubSync

github_sync = GitHubSync(
    token="your_github_token",
    owner="your_username",
    repo="your_repo"
)

# Синхронизация README и docs
github_sync.sync_documentation()
```

## 🧪 Тестирование системы

### Тест 1: Простой вопрос
```
Вопрос: "Как настроить SSL сертификат?"
Ожидаемый ответ: Пошаговая инструкция с nginx конфигурацией
```

### Тест 2: Специфичный вопрос
```
Вопрос: "Какой порт использует nginx для HTTPS?"
Ожидаемый ответ: "443" или упоминание в контексте SSL
```

### Тест 3: Вопрос без контекста
```
Вопрос: "Как приготовить борщ?"
Ожидаемый ответ: "Извините, у меня нет информации по этому вопросу"
```

## 📊 Мониторинг качества

### Проверьте статистику
```bash
curl http://localhost:8000/api/chat/stats
```

### Анализируйте логи
```bash
tail -f backend/logs/app.log
```

### Проверьте размер векторной базы
```bash
ls -la backend/chroma_db/
```

## 🔧 Настройка для продакшена

### 1. Безопасность
```env
# Измените в продакшене
SECRET_KEY=very-long-random-string-here
DEBUG=false
LOG_LEVEL=WARNING
```

### 2. Масштабирование
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
```

### 3. Мониторинг
```yaml
# Добавьте Prometheus и Grafana
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

## 🚨 Решение проблем

### Проблема: "Database connection failed"
```bash
# Проверьте PostgreSQL
docker-compose ps postgres
docker-compose logs postgres

# Перезапустите
docker-compose restart postgres
```

### Проблема: "ChromaDB initialization failed"
```bash
# Очистите векторную базу
rm -rf backend/chroma_db/
# Перезапустите backend
```

### Проблема: "LLM provider unavailable"
```bash
# Проверьте API ключи
echo $GIGACHAT_API_KEY
echo $DEEPSEEK_API_KEY
echo $OPENAI_API_KEY

# Проверьте статус моделей
curl http://localhost:8000/api/chat/models
```

### Проблема: "Frontend can't connect to backend"
```bash
# Проверьте CORS настройки
# Проверьте порты
netstat -an | grep 8000
netstat -an | grep 3000
```

## 📈 Следующие шаги

### Неделя 1: Базовое функционирование
- [ ] Добавьте 50-100 документов
- [ ] Протестируйте основные сценарии
- [ ] Настройте базовый мониторинг

### Неделя 2: Улучшение качества
- [ ] Оптимизируйте промпты
- [ ] Добавьте больше источников данных
- [ ] Настройте автоматическую синхронизацию

### Неделя 3: Масштабирование
- [ ] Настройте load balancer
- [ ] Добавьте кэширование
- [ ] Оптимизируйте производительность

### Месяц 1: Продакшен
- [ ] Настройте CI/CD
- [ ] Добавьте мониторинг и алерты
- [ ] Проведите нагрузочное тестирование

## 💡 Полезные команды

### Разработка
```bash
# Hot reload backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Hot reload frontend
npm start

# Проверка качества кода
flake8 backend/
mypy backend/
```

### Администрирование
```bash
# Очистка Docker
docker system prune -a

# Просмотр логов
docker-compose logs -f

# Перезапуск сервисов
docker-compose restart
```

### Мониторинг
```bash
# Статус системы
curl http://localhost:8000/health

# Статистика
curl http://localhost:8000/api/chat/stats

# Размер базы данных
du -sh backend/chroma_db/
```

## 🎯 Целевые метрики

### Начальный этап (1-2 недели)
- **Время ответа**: < 5 секунд
- **Точность**: > 60%
- **Покрытие**: > 40%

### Развитие (1-2 месяца)
- **Время ответа**: < 2 секунды
- **Точность**: > 80%
- **Покрытие**: > 70%

### Продакшен (3+ месяца)
- **Время ответа**: < 1 секунды
- **Точность**: > 90%
- **Покрытие**: > 85%

## 🔗 Полезные ссылки

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [ChromaDB документация](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [React документация](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

## 📞 Поддержка

Если у вас возникли проблемы:

1. **Проверьте логи**: `tail -f backend/logs/app.log`
2. **Посмотрите статус**: `curl http://localhost:8000/health`
3. **Проверьте Docker**: `docker-compose ps`
4. **Создайте issue** в GitHub репозитории

Удачи с вашей RAG системой! 🚀
