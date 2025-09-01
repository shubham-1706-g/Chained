# Deployment Guide for FlowForge Python API

This comprehensive guide covers deploying the FlowForge Python API in various environments, from development to production, with best practices for scalability, security, and monitoring.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [On-Premises Deployment](#on-premises-deployment)
5. [Configuration Management](#configuration-management)
6. [Database Setup](#database-setup)
7. [Load Balancing](#load-balancing)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Hardening](#security-hardening)
10. [Backup & Recovery](#backup--recovery)
11. [Scaling Strategies](#scaling-strategies)
12. [Troubleshooting](#troubleshooting)

## Deployment Options

### Quick Start (Development)

For development and testing:

```bash
# Clone repository
git clone https://github.com/flowforge/python-api.git
cd python-api

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run the application
python main.py
```

### Production Options

| Method | Best For | Complexity | Scalability |
|--------|----------|------------|-------------|
| Docker | Small-medium deployments | Low | Medium |
| Kubernetes | Large-scale deployments | High | High |
| AWS ECS/Fargate | Cloud-native AWS users | Medium | High |
| Google Cloud Run | Serverless deployments | Low | Auto |
| Heroku | Simple deployments | Low | Low-Medium |
| On-premises | Full control, compliance | High | Variable |

## Docker Deployment

### Basic Docker Setup

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  flowforge-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=your-api-key
      - DATABASE_URL=postgresql://user:pass@db:5432/flowforge
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=flowforge
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

**Multi-stage Dockerfile** (Production):
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
WORKDIR /app
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Commands

```bash
# Build the image
docker build -t flowforge-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e API_KEY=your-key \
  -e DATABASE_URL=postgresql://localhost/db \
  flowforge-api

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f flowforge-api

# Scale the service
docker-compose up -d --scale flowforge-api=3

# Update deployment
docker-compose build --no-cache
docker-compose up -d
```

## Cloud Deployment

### AWS ECS/Fargate

**ecs-task-definition.json**:
```json
{
  "family": "flowforge-api",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "flowforge-api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/flowforge-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_KEY", "value": "${API_KEY}"},
        {"name": "DATABASE_URL", "value": "${DATABASE_URL}"},
        {"name": "REDIS_URL", "value": "${REDIS_URL}"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/flowforge-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

**AWS CLI Deployment**:
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster flowforge-cluster \
  --service-name flowforge-api-service \
  --task-definition flowforge-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}"

# Update service
aws ecs update-service \
  --cluster flowforge-cluster \
  --service flowforge-api-service \
  --task-definition flowforge-api-v2 \
  --force-new-deployment
```

### Google Cloud Run

**Cloud Build Configuration**:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/flowforge-api:$COMMIT_SHA', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/flowforge-api:$COMMIT_SHA']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - run
      - deploy
      - flowforge-api
      - --image=gcr.io/$PROJECT_ID/flowforge-api:$COMMIT_SHA
      - --platform=managed
      - --region=us-central1
      - --allow-unauthenticated
      - --set-env-vars=API_KEY=${_API_KEY},DATABASE_URL=${_DATABASE_URL}
      - --memory=1Gi
      - --cpu=1
      - --max-instances=10
      - --concurrency=80
```

**Deploy Command**:
```bash
gcloud run deploy flowforge-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars API_KEY=your-key,DATABASE_URL=postgres://... \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --concurrency 80
```

### Azure Container Instances

**Azure CLI Deployment**:
```bash
# Create resource group
az group create --name flowforge-rg --location eastus

# Create container instance
az container create \
  --resource-group flowforge-rg \
  --name flowforge-api \
  --image your-registry.azurecr.io/flowforge-api:latest \
  --cpu 1 \
  --memory 1 \
  --registry-login-server your-registry.azurecr.io \
  --registry-username your-username \
  --registry-password your-password \
  --environment-variables API_KEY=your-key DATABASE_URL=postgres://... \
  --ports 8000 \
  --dns-name-label flowforge-api \
  --query ipAddress.fqdn
```

## On-Premises Deployment

### System Requirements

```bash
# Minimum requirements
CPU: 2 cores
RAM: 4GB
Storage: 20GB SSD
Network: 100Mbps

# Recommended for production
CPU: 4+ cores
RAM: 8GB+
Storage: 100GB+ SSD
Network: 1Gbps
```

### Ubuntu/Debian Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# Create application user
sudo useradd --create-home --shell /bin/bash flowforge
sudo usermod -aG www-data flowforge

# Set up application directory
sudo mkdir -p /opt/flowforge
sudo chown flowforge:flowforge /opt/flowforge
```

### Nginx Configuration

**/etc/nginx/sites-available/flowforge**:
```nginx
upstream flowforge_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req zone=api burst=10 nodelay;

    location / {
        proxy_pass http://flowforge_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### Systemd Service

**/etc/systemd/system/flowforge-api.service**:
```ini
[Unit]
Description=FlowForge Python API
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=flowforge
Group=flowforge
WorkingDirectory=/opt/flowforge
Environment=PATH=/opt/flowforge/venv/bin
Environment=API_KEY=your-api-key
Environment=DATABASE_URL=postgresql://user:pass@localhost/flowforge
Environment=REDIS_URL=redis://localhost:6379
ExecStart=/opt/flowforge/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Process Manager (Supervisor)

**/etc/supervisor/conf.d/flowforge-api.conf**:
```ini
[program:flowforge-api]
command=/opt/flowforge/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
directory=/opt/flowforge
user=flowforge
autostart=true
autorestart=true
redirect_stderr=true
environment=API_KEY="your-api-key",DATABASE_URL="postgresql://...",REDIS_URL="redis://..."
stdout_logfile=/var/log/supervisor/flowforge-api.log
stderr_logfile=/var/log/supervisor/flowforge-api-error.log
```

## Configuration Management

### Environment Variables

**.env file structure**:
```bash
# Application
API_KEY=your-secure-api-key
SECRET_KEY=your-secret-key-for-sessions
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://host:port/db
REDIS_PASSWORD=your-redis-password

# External Services
OPENAI_API_KEY=sk-your-openai-key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
DATADOG_API_KEY=your-datadog-key

# Security
ALLOWED_HOSTS=api.yourdomain.com,api-staging.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com,https://app-staging.yourdomain.com

# Performance
MAX_WORKERS=4
WORKER_TIMEOUT=30
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/flowforge/api.log

# Features
ENABLE_WEBHOOKS=true
ENABLE_SCHEDULER=true
ENABLE_METRICS=true
```

### Configuration Classes

**config.py**:
```python
from pydantic import BaseSettings, Field
from typing import List, Optional
import secrets

class DatabaseConfig(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(20, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(30, env="DATABASE_MAX_OVERFLOW")
    echo: bool = Field(False, env="DATABASE_ECHO")

class RedisConfig(BaseSettings):
    url: str = Field(..., env="REDIS_URL")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    db: int = Field(0, env="REDIS_DB")

class ExternalServicesConfig(BaseSettings):
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    smtp_server: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")

class SecurityConfig(BaseSettings):
    api_key: str = Field(..., env="API_KEY")
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    allowed_hosts: List[str] = Field(["localhost"], env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")

class MonitoringConfig(BaseSettings):
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    datadog_api_key: Optional[str] = Field(None, env="DATADOG_API_KEY")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")

class AppConfig(BaseSettings):
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")
    max_workers: int = Field(4, env="MAX_WORKERS")
    worker_timeout: int = Field(30, env="WORKER_TIMEOUT")

    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    external_services: ExternalServicesConfig = ExternalServicesConfig()
    security: SecurityConfig = SecurityConfig()
    monitoring: MonitoringConfig = MonitoringConfig()

# Global config instance
config = AppConfig()
```

## Database Setup

### PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE flowforge;
CREATE USER flowforge_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE flowforge TO flowforge_user;
ALTER USER flowforge_user CREATEDB;

# Exit PostgreSQL
\q

# Run migrations
cd /opt/flowforge
source venv/bin/activate
alembic upgrade head
```

### Redis Setup

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: supervised systemd
# Set: requirepass your-password
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server

# Enable Redis on boot
sudo systemctl enable redis-server
```

## Load Balancing

### Nginx Load Balancer

```nginx
upstream flowforge_api {
    least_conn;
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 weight=1 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://flowforge_api;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health checks
        health_check interval=10s fails=3 passes=2 uri=/health;
    }
}
```

### HAProxy Configuration

**/etc/haproxy/haproxy.cfg**:
```haproxy
frontend flowforge_api
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/flowforge.pem
    default_backend flowforge_backend

backend flowforge_backend
    balance leastconn
    option httpchk GET /health
    http-check expect status 200
    default-server inter 10s fall 3 rise 2

    server api1 127.0.0.1:8000 check maxconn 100
    server api2 127.0.0.1:8001 check maxconn 100
    server api3 127.0.0.1:8002 check maxconn 100
    server api4 127.0.0.1:8003 check maxconn 100
```

## Monitoring & Observability

### Prometheus Metrics

**metrics.py**:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

WORKFLOW_EXECUTIONS = Counter(
    'workflow_executions_total',
    'Total workflow executions',
    ['status', 'trigger_type']
)

ACTION_EXECUTIONS = Counter(
    'action_executions_total',
    'Total action executions',
    ['action_type', 'status']
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        ACTIVE_CONNECTIONS.inc()

        response = await call_next(request)

        process_time = time.time() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)

        ACTIVE_CONNECTIONS.dec()

        return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

**health.py**:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis
import aiohttp
import time
from typing import Dict, Any

router = APIRouter()

async def check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        # Database health check
        start_time = time.time()
        # Your database query here
        response_time = time.time() - start_time

        return {
            "status": "healthy",
            "response_time": f"{response_time:.3f}s"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        redis_client = redis.Redis.from_url(config.redis.url)
        redis_client.ping()

        return {"status": "healthy"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_external_services() -> Dict[str, Any]:
    """Check external service connectivity."""
    services = {}

    # Check OpenAI if configured
    if config.external_services.openai_api_key:
        try:
            async with aiohttp.ClientSession() as session:
                # Simple API call to check connectivity
                services["openai"] = {"status": "healthy"}
        except Exception as e:
            services["openai"] = {"status": "unhealthy", "error": str(e)}

    return services

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    start_time = time.time()

    database = await check_database()
    redis_check = await check_redis()
    external_services = await check_external_services()

    overall_status = "healthy"
    if any(service.get("status") == "unhealthy"
           for service in [database, redis_check] + list(external_services.values())):
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "response_time": f"{time.time() - start_time:.3f}s",
        "version": "1.0.0",
        "checks": {
            "database": database,
            "redis": redis_check,
            "external_services": external_services
        }
    }

@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    # Check if service is ready to accept traffic
    try:
        # Quick database check
        await check_database()
        return {"status": "ready"}
    except:
        return {"status": "not ready"}, 503
```

### Logging Configuration

**logging_config.py**:
```python
import logging
import logging.config
from pythonjsonlogger import jsonlogger
import sys

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['message'] = record.getMessage()

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': CustomJsonFormatter,
            'format': '%(timestamp)s %(level)s %(logger)s %(message)s'
        },
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': sys.stdout
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/flowforge/api.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/flowforge/error.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json',
            'level': 'ERROR'
        }
    },
    'loggers': {
        'flowforge': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'sqlalchemy': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO'
    }
}

def setup_logging():
    """Setup logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)

    # Set up specific loggers
    logger = logging.getLogger('flowforge')
    logger.info("FlowForge logging initialized")
```

## Security Hardening

### SSL/TLS Configuration

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Security headers
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### API Key Security

```python
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt

class APIKeyManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_api_key(self, user_id: str, scopes: list = None) -> str:
        """Create a new API key."""
        payload = {
            'user_id': user_id,
            'scopes': scopes or ['read', 'write'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=365)
        }

        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_api_key(self, api_key: str) -> Optional[dict]:
        """Verify and decode API key."""
        try:
            payload = jwt.decode(api_key, self.secret_key, algorithms=['HS256'])

            # Check expiration
            if datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
                return None

            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def rotate_api_key(self, old_key: str) -> Optional[str]:
        """Rotate an existing API key."""
        payload = self.verify_api_key(old_key)
        if not payload:
            return None

        # Create new key with same payload
        payload['iat'] = datetime.utcnow()
        payload['exp'] = datetime.utcnow() + timedelta(days=365)

        return jwt.encode(payload, self.secret_key, algorithm='HS256')
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Global rate limits
@limiter.limit("100/minute")
@app.get("/api/v1/actions/execute")
async def execute_action():
    pass

@limiter.limit("50/minute")
@app.post("/api/v1/flows/execute")
async def execute_flow():
    pass

# Per-user rate limits
@limiter.limit("10/minute", key_func=lambda: get_current_user_id())
@app.post("/api/v1/triggers/create")
async def create_trigger():
    pass

# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "retry_after": exc.retry_after
            }
        },
        headers={"Retry-After": str(exc.retry_after)}
    )

# Add middleware
app.add_middleware(SlowAPIMiddleware)
```

## Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# PostgreSQL backup script

BACKUP_DIR="/var/backups/flowforge"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/flowforge_$TIMESTAMP.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U flowforge_user -d flowforge > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE.gz s3://your-backup-bucket/flowforge/
```

### Automated Backup with Cron

```bash
# Edit crontab
crontab -e

# Add backup job (daily at 2 AM)
0 2 * * * /path/to/backup-script.sh

# Add log rotation
0 3 * * * logrotate /etc/logrotate.d/flowforge
```

### Recovery Procedure

```bash
#!/bin/bash
# Database recovery script

BACKUP_FILE="/var/backups/flowforge/flowforge_20240115_020000.sql.gz"

# Stop application
sudo systemctl stop flowforge-api

# Restore database
gunzip -c $BACKUP_FILE | psql -h localhost -U flowforge_user -d flowforge

# Start application
sudo systemctl start flowforge-api

# Verify restoration
curl http://localhost:8000/health
```

## Scaling Strategies

### Horizontal Scaling

```python
# Gunicorn configuration for multiple workers
# gunicorn.conf.py
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 10
preload_app = True
```

### Database Scaling

```sql
-- PostgreSQL connection pooling with PgBouncer
[databases]
flowforge = host=localhost port=5432 dbname=flowforge

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
reserve_pool_size = 5
```

### Redis Clustering

```redis.conf
# Redis cluster configuration
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
appendfilename "appendonly.aof"
```

### Load Testing

```bash
# Install locust for load testing
pip install locust

# locustfile.py
from locust import HttpUser, task, between

class FlowForgeUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def execute_action(self):
        self.client.post("/api/v1/actions/execute", json={
            "action_type": "http",
            "config": {"method": "GET", "url": "https://httpbin.org/get"}
        })

    @task
    def get_health(self):
        self.client.get("/health")

# Run load test
locust -f locustfile.py --host http://localhost:8000
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   ps aux --sort=-%mem | head

   # Monitor with htop
   htop

   # Check Python memory
   python -c "import psutil; print(psutil.virtual_memory())"
   ```

2. **Slow Response Times**
   ```bash
   # Check database connections
   psql -c "SELECT count(*) FROM pg_stat_activity;"

   # Monitor Redis
   redis-cli info | grep connected_clients

   # Check system load
   uptime
   ```

3. **Connection Pool Exhaustion**
   ```python
   # Monitor connection pools
   from sqlalchemy import text

   with engine.connect() as conn:
       result = conn.execute(text("SELECT * FROM pg_stat_activity"))
       print(f"Active connections: {len(result.fetchall())}")
   ```

4. **Webhook Delivery Issues**
   ```bash
   # Check webhook logs
   grep webhook /var/log/flowforge/api.log | tail -20

   # Test webhook manually
   curl -X POST https://your-webhook-url \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### Debugging Commands

```bash
# Check application status
sudo systemctl status flowforge-api

# View recent logs
sudo journalctl -u flowforge-api -f

# Check network connections
netstat -tlnp | grep :8000

# Monitor disk usage
df -h

# Check CPU usage
top -p $(pgrep -f uvicorn)

# Debug database queries
psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Performance Tuning

```python
# Uvicorn configuration for production
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornHorker \
  --loop uvloop \
  --http httptools \
  --ws none \
  --log-level info \
  --access-log \
  --proxy-headers \
  --forwarded-allow-ips "*"

# Gunicorn alternative
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile -
```

---

This deployment guide provides comprehensive instructions for deploying FlowForge Python API in various environments. For specific cloud provider documentation or advanced configurations, refer to the [official documentation](https://docs.flowforge.com) or community forums.

Remember to always test your deployment in a staging environment before deploying to production! 🚀

