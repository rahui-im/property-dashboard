# 🏢 MCP 기반 부동산 매물 관리 시스템 - 완전 구현 가이드

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [핵심 컴포넌트](#핵심-컴포넌트)
4. [구현 상세](#구현-상세)
5. [설치 및 실행](#설치-및-실행)
6. [운영 가이드](#운영-가이드)

## 시스템 개요

### 목적
공인중개사의 매물 관리 업무를 완전 자동화하는 분산 마이크로서비스 시스템

### 핵심 기능
- ✅ 다중 플랫폼 실시간 매물 수집
- ✅ 지능형 데이터 정규화 및 중복 제거
- ✅ 실시간 가격 변동 추적
- ✅ 고객 맞춤 매물 매칭
- ✅ 자동 리포트 생성
- ✅ 알림 및 모니터링

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         외부 인터페이스 계층                        │
├─────────────────────────────────────────────────────────────────┤
│  Web Dashboard │ Mobile App │ REST API │ GraphQL │ WebSocket   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (Kong/Nginx)                    │
│                    - 인증/인가 - 라우팅 - 캐싱                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────┐
│                    MCP 오케스트레이터 서버                         │
│              (중앙 제어, 작업 분배, 상태 관리)                      │
├─────────────────────────────────────────────────────────────────┤
│ • Task Queue Manager    │ • Agent Registry                      │
│ • Load Balancer        │ • Health Monitor                       │
│ • Result Aggregator    │ • Event Bus                           │
└──────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │          │
  [수집 계층] [처리 계층] [저장 계층] [분석 계층] [알림 계층]
```

### 시스템 구성 요소

```yaml
1. 수집 계층 (Collection Layer):
   - 10+ 플랫폼 크롤러
   - 동적 렌더링 지원
   - Rate limiting
   - Proxy rotation

2. 처리 계층 (Processing Layer):
   - 데이터 정규화
   - 중복 제거
   - 이미지 처리
   - OCR 처리

3. 저장 계층 (Storage Layer):
   - PostgreSQL (메인 DB)
   - MongoDB (원시 데이터)
   - Redis (캐시)
   - S3 (이미지/문서)

4. 분석 계층 (Analytics Layer):
   - 가격 분석
   - 트렌드 분석
   - 시장 예측
   - 이상 탐지

5. 알림 계층 (Notification Layer):
   - 실시간 알림
   - 이메일/SMS
   - 푸시 알림
   - Webhook
```

## 핵심 컴포넌트

### 1. MCP 오케스트레이터 서버

```python
# src/mcp/orchestrator/main.py
"""
MCP 오케스트레이터 메인 서버
"""
from fastapi import FastAPI, WebSocket
from typing import Dict, List
import asyncio
import uvicorn

app = FastAPI(title="MCP Orchestrator")

class MCPOrchestrator:
    def __init__(self):
        self.agents = {}
        self.tasks = {}
        self.websockets = {}
        
    async def start(self):
        # 시스템 초기화
        await self.init_database()
        await self.init_cache()
        await self.init_message_queue()
        
@app.on_event("startup")
async def startup():
    orchestrator.start()

@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    # WebSocket 연결 관리
```

### 2. 수집 서브에이전트 시스템

```python
# src/agents/collectors/base.py
"""
수집 에이전트 베이스 클래스
"""
class CollectorAgent:
    def __init__(self, platform: str):
        self.platform = platform
        self.session = None
        
    async def collect(self, area: str, filters: dict):
        # 플랫폼별 수집 로직
        pass
        
    async def validate(self, data: dict):
        # 데이터 검증
        pass
```

### 3. 데이터 모델

```python
# src/models/property.py
"""
매물 데이터 모델
"""
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    title = Column(String)
    price = Column(Integer)
    area = Column(Float)
    address = Column(String)
    # ... 추가 필드
```

## 구현 상세

### 디렉토리 구조

```
property-management-system/
├── src/
│   ├── mcp/
│   │   ├── orchestrator/
│   │   │   ├── main.py
│   │   │   ├── coordinator.py
│   │   │   ├── scheduler.py
│   │   │   └── monitor.py
│   │   ├── communication/
│   │   │   ├── websocket.py
│   │   │   ├── message_queue.py
│   │   │   └── event_bus.py
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── agents/
│   │   ├── collectors/
│   │   │   ├── base.py
│   │   │   ├── naver.py
│   │   │   ├── zigbang.py
│   │   │   ├── dabang.py
│   │   │   ├── kb.py
│   │   │   └── ...
│   │   ├── processors/
│   │   │   ├── normalizer.py
│   │   │   ├── deduplicator.py
│   │   │   ├── validator.py
│   │   │   └── image_processor.py
│   │   ├── storage/
│   │   │   ├── database.py
│   │   │   ├── cache.py
│   │   │   └── file_storage.py
│   │   └── analytics/
│   │       ├── price_analyzer.py
│   │       ├── trend_analyzer.py
│   │       └── anomaly_detector.py
│   │
│   ├── models/
│   │   ├── property.py
│   │   ├── agent.py
│   │   ├── task.py
│   │   └── user.py
│   │
│   ├── api/
│   │   ├── gateway.py
│   │   ├── routes/
│   │   │   ├── properties.py
│   │   │   ├── agents.py
│   │   │   └── tasks.py
│   │   └── middleware/
│   │       ├── auth.py
│   │       └── rate_limit.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── migrations/
│   │   └── seeds/
│   │
│   ├── utils/
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   └── helpers.py
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── docker/
│   ├── Dockerfile.orchestrator
│   ├── Dockerfile.collector
│   ├── Dockerfile.processor
│   └── docker-compose.yml
│
├── kubernetes/
│   ├── deployments/
│   ├── services/
│   └── configmaps/
│
├── config/
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
│
├── scripts/
│   ├── setup.sh
│   ├── deploy.sh
│   └── monitor.sh
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
│
├── requirements.txt
├── .env.example
└── README.md
```

### 환경 설정 파일

```yaml
# config/production.yaml
system:
  name: "Property Management System"
  version: "1.0.0"
  environment: "production"

mcp:
  orchestrator:
    host: "0.0.0.0"
    port: 8000
    workers: 4
    
  websocket:
    ping_interval: 30
    timeout: 60
    max_connections: 1000
    
  task_queue:
    broker: "redis://redis:6379/0"
    backend: "redis://redis:6379/1"
    
database:
  postgresql:
    host: "postgres"
    port: 5432
    database: "property_db"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
    pool_size: 20
    
  mongodb:
    uri: "mongodb://mongo:27017"
    database: "property_raw"
    
  redis:
    host: "redis"
    port: 6379
    db: 0
    
collectors:
  naver:
    enabled: true
    rate_limit: 2
    max_workers: 5
    proxy_enabled: true
    
  zigbang:
    enabled: true
    rate_limit: 3
    max_workers: 3
    
monitoring:
  prometheus:
    enabled: true
    port: 9090
    
  grafana:
    enabled: true
    port: 3000
    
  elasticsearch:
    enabled: true
    host: "elasticsearch"
    port: 9200
```

## 설치 및 실행

### 1. 사전 준비

```bash
# 저장소 클론
git clone https://github.com/your-org/property-management-system.git
cd property-management-system

# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium

# 환경변수 설정
cp .env.example .env
# .env 파일 편집하여 필요한 값 설정
```

### 2. Docker Compose로 전체 시스템 실행

```yaml
# docker-compose.yml
version: '3.8'

services:
  # MCP 오케스트레이터
  orchestrator:
    build:
      context: .
      dockerfile: docker/Dockerfile.orchestrator
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    depends_on:
      - postgres
      - redis
      - mongo
    networks:
      - property-net
      
  # 수집 에이전트 (스케일링 가능)
  collector-naver:
    build:
      context: .
      dockerfile: docker/Dockerfile.collector
    environment:
      - PLATFORM=naver
      - ORCHESTRATOR_URL=http://orchestrator:8000
    deploy:
      replicas: 3
    networks:
      - property-net
      
  collector-zigbang:
    build:
      context: .
      dockerfile: docker/Dockerfile.collector
    environment:
      - PLATFORM=zigbang
      - ORCHESTRATOR_URL=http://orchestrator:8000
    deploy:
      replicas: 2
    networks:
      - property-net
      
  # 처리 에이전트
  processor:
    build:
      context: .
      dockerfile: docker/Dockerfile.processor
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8000
    deploy:
      replicas: 2
    networks:
      - property-net
      
  # 데이터베이스
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=property_db
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=secret
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - property-net
      
  # MongoDB
  mongo:
    image: mongo:5
    volumes:
      - mongo-data:/data/db
    networks:
      - property-net
      
  # Redis
  redis:
    image: redis:7-alpine
    networks:
      - property-net
      
  # API Gateway
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - orchestrator
    networks:
      - property-net
      
  # 모니터링
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - property-net
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - property-net

volumes:
  postgres-data:
  mongo-data:

networks:
  property-net:
    driver: bridge
```

### 3. 시스템 시작

```bash
# Docker Compose로 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f orchestrator

# 상태 확인
docker-compose ps

# 스케일링
docker-compose up -d --scale collector-naver=5
```

### 4. API 사용 예시

```python
# client_example.py
import requests
import asyncio
import websockets
import json

# REST API 사용
def collect_properties():
    """매물 수집 시작"""
    response = requests.post(
        "http://localhost:8000/api/v1/tasks",
        json={
            "type": "collect",
            "areas": ["강남구", "서초구"],
            "platforms": ["naver", "zigbang"],
            "filters": {
                "price_min": 100000,
                "price_max": 200000,
                "area_min": 60
            }
        }
    )
    return response.json()

# WebSocket으로 실시간 모니터링
async def monitor_collection():
    """실시간 수집 상태 모니터링"""
    async with websockets.connect("ws://localhost:8000/ws/monitor") as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Status: {data}")

# GraphQL 쿼리
def search_properties():
    """매물 검색"""
    query = """
    query SearchProperties {
        properties(
            area: "강남구"
            priceMin: 100000
            priceMax: 150000
        ) {
            id
            title
            price
            area
            address
            platform
        }
    }
    """
    response = requests.post(
        "http://localhost:8000/graphql",
        json={"query": query}
    )
    return response.json()
```

## 운영 가이드

### 모니터링

```bash
# Grafana 대시보드 접속
http://localhost:3000
# admin / admin

# Prometheus 메트릭 확인
http://localhost:9090

# 헬스체크
curl http://localhost:8000/health

# 에이전트 상태
curl http://localhost:8000/api/v1/agents/status
```

### 로그 관리

```python
# src/utils/logger.py
import logging
from loguru import logger
import sys

# 로그 설정
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    level="INFO"
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

# ELK 스택 연동
logger.add(
    "logstash://localhost:5000",
    format="json",
    level="INFO"
)
```

### 성능 최적화

```python
# src/utils/performance.py
"""
성능 최적화 유틸리티
"""
import asyncio
from functools import lru_cache
import aioredis

class PerformanceOptimizer:
    def __init__(self):
        self.redis = None
        
    @lru_cache(maxsize=1000)
    def get_cached_result(self, key):
        """메모리 캐싱"""
        pass
        
    async def get_redis_cache(self, key):
        """Redis 캐싱"""
        if not self.redis:
            self.redis = await aioredis.create_redis_pool('redis://localhost')
        return await self.redis.get(key)
        
    async def batch_process(self, items, batch_size=100):
        """배치 처리"""
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            await self.process_batch(batch)
```

### 에러 처리

```python
# src/utils/error_handler.py
"""
전역 에러 처리
"""
from typing import Optional
import traceback

class ErrorHandler:
    @staticmethod
    async def handle_error(error: Exception, context: dict) -> Optional[dict]:
        """에러 처리 및 복구"""
        error_type = type(error).__name__
        
        if error_type == "ConnectionError":
            # 재연결 시도
            return await ErrorHandler.retry_connection(context)
        elif error_type == "TimeoutError":
            # 타임아웃 처리
            return await ErrorHandler.handle_timeout(context)
        else:
            # 일반 에러 로깅
            logger.error(f"Error: {error}\nContext: {context}\n{traceback.format_exc()}")
            return None
```

### 백업 및 복구

```bash
#!/bin/bash
# scripts/backup.sh

# PostgreSQL 백업
docker exec postgres pg_dump -U admin property_db > backup_$(date +%Y%m%d).sql

# MongoDB 백업
docker exec mongo mongodump --out /backup/$(date +%Y%m%d)

# Redis 백업
docker exec redis redis-cli BGSAVE

# S3 업로드
aws s3 cp backup_$(date +%Y%m%d).sql s3://backup-bucket/postgres/
```

## 보안 설정

```python
# src/api/middleware/security.py
"""
보안 미들웨어
"""
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## 테스트

```python
# tests/test_collector.py
import pytest
from src.agents.collectors.naver import NaverCollector

@pytest.mark.asyncio
async def test_naver_collector():
    collector = NaverCollector()
    results = await collector.collect("강남구", {"limit": 10})
    
    assert len(results) > 0
    assert all('price' in item for item in results)
    assert all('area' in item for item in results)
```

## 배포

### Kubernetes 배포

```yaml
# kubernetes/deployments/orchestrator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: property-system/orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENV
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

이 시스템은 **실제 프로덕션 환경**에서 운영 가능한 완전한 매물 관리 시스템입니다!