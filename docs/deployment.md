# Руководство по развертыванию

## Обзор

Данное руководство описывает процесс развертывания Chatbot Support в различных средах.

## Требования

### Системные требования

- **CPU**: 4+ ядра
- **RAM**: 8+ GB
- **Storage**: 20+ GB свободного места
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Программные зависимости

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+ (опционально)

## Локальная разработка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd chatbot-support
```

### 2. Настройка переменных окружения

```bash
# Backend
cp backend/env.example backend/.env
# Отредактируйте .env файл с вашими API ключами
```

### 3. Запуск с Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Инициализация базы данных

```bash
# Вход в контейнер backend
docker-compose exec backend bash

# Запуск скрипта инициализации
python scripts/setup_db.py
```

### 5. Проверка работы

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Production развертывание

### Вариант 1: Docker Compose (рекомендуется)

#### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

#### 2. Настройка production конфигурации

Создайте `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: chatbot_postgres_prod
    environment:
      POSTGRES_DB: chatbot_support
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - chatbot_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: chatbot_redis_prod
    volumes:
      - redis_data:/data
    networks:
      - chatbot_network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: chatbot_backend_prod
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/chatbot_support
      - REDIS_URL=redis://redis:6379
      - CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db
      - LOG_FILE=/app/logs/chatbot.log
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=false
      - GIGACHAT_API_KEY=${GIGACHAT_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - backend_data:/app/data
      - backend_logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - chatbot_network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: chatbot_frontend_prod
    environment:
      - REACT_APP_API_URL=${API_URL}
      - REACT_APP_WS_URL=${WS_URL}
    depends_on:
      - backend
    networks:
      - chatbot_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: chatbot_nginx_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - chatbot_network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  backend_data:
  backend_logs:

networks:
  chatbot_network:
    driver: bridge
```

#### 3. Создание .env файла

```bash
# Production environment variables
DB_USER=chatbot_user
DB_PASSWORD=secure_password_here
GIGACHAT_API_KEY=your_gigachat_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key
API_URL=https://your-domain.com/api
WS_URL=wss://your-domain.com/ws
```

#### 4. Настройка Nginx

Создайте `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### 5. Запуск production

```bash
# Сборка и запуск
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f
```

### Вариант 2: Kubernetes

#### 1. Создание namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chatbot-support
```

#### 2. ConfigMap и Secret

```yaml
# config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
  namespace: chatbot-support
data:
  DATABASE_URL: "postgresql://chatbot_user:password@postgres:5432/chatbot_support"
  CHROMA_PERSIST_DIRECTORY: "/app/data/chroma_db"
  LOG_FILE: "/app/logs/chatbot.log"
  HOST: "0.0.0.0"
  PORT: "8000"
  DEBUG: "false"
---
apiVersion: v1
kind: Secret
metadata:
  name: chatbot-secrets
  namespace: chatbot-support
type: Opaque
data:
  GIGACHAT_API_KEY: <base64-encoded-key>
  DEEPSEEK_API_KEY: <base64-encoded-key>
  OPENAI_API_KEY: <base64-encoded-key>
  DB_PASSWORD: <base64-encoded-password>
```

#### 3. PostgreSQL Deployment

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: chatbot-support
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: chatbot_support
        - name: POSTGRES_USER
          value: chatbot_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: chatbot-secrets
              key: DB_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: chatbot-support
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: chatbot-support
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

#### 4. Backend Deployment

```yaml
# backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: chatbot-support
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: chatbot-backend:latest
        envFrom:
        - configMapRef:
            name: chatbot-config
        - secretRef:
            name: chatbot-secrets
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: backend-storage
          mountPath: /app/data
        - name: backend-logs
          mountPath: /app/logs
      volumes:
      - name: backend-storage
        persistentVolumeClaim:
          claimName: backend-pvc
      - name: backend-logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: chatbot-support
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backend-pvc
  namespace: chatbot-support
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
```

#### 5. Frontend Deployment

```yaml
# frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: chatbot-support
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: chatbot-frontend:latest
        env:
        - name: REACT_APP_API_URL
          value: "https://api.your-domain.com"
        - name: REACT_APP_WS_URL
          value: "wss://api.your-domain.com"
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: chatbot-support
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
```

#### 6. Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chatbot-ingress
  namespace: chatbot-support
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: chatbot-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

#### 7. Применение конфигурации

```bash
kubectl apply -f namespace.yaml
kubectl apply -f config.yaml
kubectl apply -f postgres.yaml
kubectl apply -f backend.yaml
kubectl apply -f frontend.yaml
kubectl apply -f ingress.yaml
```

## Мониторинг и логирование

### Prometheus + Grafana

```yaml
# monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: chatbot-support
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'chatbot-backend'
      static_configs:
      - targets: ['backend:8000']
```

### Логирование с ELK Stack

```yaml
# logging.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
  namespace: chatbot-support
spec:
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
        env:
        - name: discovery.type
          value: single-node
        ports:
        - containerPort: 9200
```

## Backup и восстановление

### Backup базы данных

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump -U chatbot_user chatbot_support > $BACKUP_DIR/db_backup_$DATE.sql

# Backup vector store
tar -czf $BACKUP_DIR/vector_store_$DATE.tar.gz -C ./data/chroma_db .

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Восстановление

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Restore PostgreSQL
docker-compose exec -T postgres psql -U chatbot_user chatbot_support < $BACKUP_FILE

# Restore vector store (if needed)
# tar -xzf vector_store_backup.tar.gz -C ./data/chroma_db/
```

## Обновление

### Docker Compose

```bash
# Остановка сервисов
docker-compose down

# Обновление кода
git pull

# Пересборка образов
docker-compose build --no-cache

# Запуск с новой версией
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### Kubernetes

```bash
# Обновление образа
kubectl set image deployment/backend backend=chatbot-backend:new-version -n chatbot-support
kubectl set image deployment/frontend frontend=chatbot-frontend:new-version -n chatbot-support

# Проверка статуса обновления
kubectl rollout status deployment/backend -n chatbot-support
kubectl rollout status deployment/frontend -n chatbot-support

# Откат при необходимости
kubectl rollout undo deployment/backend -n chatbot-support
```

## Troubleshooting

### Частые проблемы

1. **Ошибка подключения к базе данных**
   ```bash
   # Проверка статуса PostgreSQL
   docker-compose ps postgres
   docker-compose logs postgres
   ```

2. **Проблемы с WebSocket**
   ```bash
   # Проверка WebSocket соединений
   curl http://localhost:8000/ws/status
   ```

3. **Ошибки AI моделей**
   ```bash
   # Проверка доступных моделей
   curl http://localhost:8000/api/chat/models
   ```

4. **Проблемы с векторной базой**
   ```bash
   # Проверка статистики
   curl http://localhost:8000/api/chat/stats
   ```

### Логи

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend

# Kubernetes логи
kubectl logs -f deployment/backend -n chatbot-support
kubectl logs -f deployment/frontend -n chatbot-support
```

## Безопасность

### SSL/TLS сертификаты

```bash
# Let's Encrypt с certbot
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall

```bash
# UFW на Ubuntu
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Обновления безопасности

```bash
# Регулярные обновления
sudo apt update && sudo apt upgrade -y

# Обновление Docker образов
docker-compose pull
docker-compose up -d
```
