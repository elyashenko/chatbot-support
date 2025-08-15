#!/usr/bin/env python3
"""
Скрипт для добавления тестовых документов в векторную базу
Запуск: python scripts/add_test_docs.py
"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку backend в Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.models.vector_store import ChromaVectorStore
from app.models.embeddings import document_chunker

def create_test_documents():
    """Создает тестовые документы для демонстрации RAG системы"""
    
    documents = [
        {
            "title": "SSL сертификат настройка",
            "content": """# Как настроить SSL сертификат

## Шаг 1: Получение сертификата
1. Установите certbot: `sudo apt install certbot`
2. Получите сертификат: `sudo certbot certonly --standalone -d yourdomain.com`
3. Проверьте статус: `sudo certbot certificates`

## Шаг 2: Настройка nginx
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
}
```

## Шаг 3: Автообновление
Добавьте в crontab: `0 12 * * * /usr/bin/certbot renew --quiet`

## Шаг 4: Проверка
Проверьте SSL: https://www.ssllabs.com/ssltest/""",
            "category": "DevOps",
            "tags": ["ssl", "nginx", "security", "letsencrypt"]
        },
        {
            "title": "Docker оптимизация",
            "content": """# Оптимизация Docker контейнеров

## Многоэтапная сборка
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Production stage
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

## Оптимизация размера
- Используйте alpine образы
- Удаляйте ненужные файлы
- Объединяйте RUN команды
- Используйте .dockerignore

## Мониторинг
```bash
# Размер образов
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Использование ресурсов
docker stats

# Анализ слоев
docker history image_name
```""",
            "category": "DevOps",
            "tags": ["docker", "optimization", "containers", "ci-cd"]
        },
        {
            "title": "PostgreSQL производительность",
            "content": """# Оптимизация PostgreSQL

## Индексы
```sql
-- Создание индекса
CREATE INDEX idx_users_email ON users(email);

-- Составной индекс
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);

-- Частичный индекс
CREATE INDEX idx_active_users ON users(id) WHERE active = true;
```

## Анализ запросов
```sql
-- EXPLAIN для анализа
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM users WHERE email = 'test@example.com';

-- Статистика по таблицам
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables;
```

## Настройки postgresql.conf
```ini
# Память
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9""",
            "category": "Database",
            "tags": ["postgresql", "performance", "indexes", "optimization"]
        }
    ]
    
    return documents

def add_documents_to_vector_store():
    """Добавляет тестовые документы в векторную базу"""
    
    try:
        # Инициализация компонентов
        vector_store = ChromaVectorStore()
        
        # Получение тестовых документов
        documents = create_test_documents()
        
        print(f"🚀 Начинаю добавление {len(documents)} документов в векторную базу...")
        
        total_chunks = 0
        
        for i, doc in enumerate(documents, 1):
            print(f"📄 Обрабатываю документ {i}/{len(documents)}: {doc['title']}")
            
            # Чанкирование документа
            chunks = document_chunker.chunk_text(doc['content'])
            total_chunks += len(chunks)
            
            # Добавление чанков в векторную базу
            for chunk_data in chunks:
                chunk_text = chunk_data['text']
                chunk_metadata = chunk_data['metadata'].copy()
                chunk_metadata.update({
                    "title": doc['title'],
                    "category": doc['category'],
                    "tags": ", ".join(doc['tags']),  # Преобразуем список в строку
                    "source": "test_docs"
                })
                
                vector_store.add_documents([{"text": chunk_text, "metadata": chunk_metadata}])
            
            print(f"   ✅ Добавлено {len(chunks)} чанков")
        
        print(f"\n🎉 Готово! Добавлено {total_chunks} чанков из {len(documents)} документов")
        
        # Проверяем статистику
        stats = vector_store.get_collection_stats()
        print(f"📊 Статистика векторной базы:")
        print(f"   - Всего документов: {stats['total_documents']}")
        print(f"   - Размер базы: {stats.get('database_size', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении документов: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция"""
    print("🔧 Скрипт добавления тестовых документов в RAG систему")
    print("=" * 60)
    
    # Проверяем, что мы в правильной директории
    if not Path.cwd().name == "backend":
        print("❌ Запустите скрипт из папки backend")
        print("   cd backend && python scripts/add_test_docs.py")
        return
    
    # Проверяем наличие .env файла
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Файл .env не найден")
        print("   Скопируйте env.example в .env и настройте переменные")
        return
    
    # Добавляем документы
    add_documents_to_vector_store()
    
    print("\n" + "=" * 60)
    print("🎯 Теперь вы можете тестировать RAG систему!")
    print("💡 Попробуйте задать вопросы:")
    print("   - 'Как настроить SSL сертификат?'")
    print("   - 'Как оптимизировать Docker контейнеры?'")
    print("   - 'Как улучшить производительность PostgreSQL?'")

if __name__ == "__main__":
    main()
