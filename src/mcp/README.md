# MCP 기반 부동산 매물 수집 서브에이전트

## 개요
MCP(Model Context Protocol) 서버를 활용한 공인중개사 업무 자동화 시스템의 첫 번째 단계로, 
다양한 부동산 플랫폼에서 매물 정보를 자동으로 수집하는 서브에이전트입니다.

## 아키텍처

```
┌─────────────────────────────────────────────┐
│            MCP Orchestrator                  │
│         (메인 에이전트 컨트롤러)              │
└─────────────┬───────────────────────────────┘
              │
              ├── Property Collection Agent
              │   ├── Naver Real Estate Collector
              │   ├── Zigbang Collector
              │   ├── Dabang Collector
              │   └── KB Real Estate Collector
              │
              ├── Data Processing Agent
              │   ├── Normalizer
              │   ├── Validator
              │   └── Deduplicator
              │
              └── Storage Agent
                  ├── Database Writer
                  ├── Cache Manager
                  └── File Exporter
```

## 기능

### 1. 매물 수집 (Property Collection)
- 네이버 부동산, 직방, 다방, KB부동산 등 주요 플랫폼 지원
- 비동기 병렬 수집으로 성능 최적화
- 동적 페이지 렌더링 지원 (Playwright 활용)
- Rate limiting 및 봇 탐지 회피

### 2. 데이터 처리 (Data Processing)
- 플랫폼별 상이한 데이터 형식 정규화
- 중복 매물 제거 및 병합
- 데이터 유효성 검증
- 가격/면적 이상치 탐지

### 3. 저장 및 관리 (Storage)
- PostgreSQL 데이터베이스 저장
- Redis 캐싱으로 중복 확인 최적화
- Excel/CSV 내보내기 지원
- 실시간 업데이트 알림

## MCP 서버 통신 프로토콜

### 메시지 형식
```json
{
  "type": "request|response|notification",
  "id": "unique-request-id",
  "method": "collect|process|store",
  "params": {
    "action": "start|stop|status",
    "target": "platform-name",
    "config": {}
  }
}
```

### 지원 메서드
- `collect.start`: 수집 시작
- `collect.stop`: 수집 중지
- `collect.status`: 수집 상태 확인
- `process.normalize`: 데이터 정규화
- `process.validate`: 데이터 검증
- `store.save`: 데이터 저장

## 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# MCP 서버 시작
python -m src.mcp.server

# 수집 에이전트 실행
python -m src.mcp.agents.collector
```

## 설정

`config/mcp_config.yaml` 파일에서 설정 관리:
```yaml
mcp:
  server:
    host: localhost
    port: 9001
  
collectors:
  naver:
    enabled: true
    rate_limit: 2  # requests per second
  zigbang:
    enabled: true
    rate_limit: 3
    
database:
  type: postgresql
  connection: postgresql://user:pass@localhost/realestate
  
cache:
  type: redis
  connection: redis://localhost:6379
```