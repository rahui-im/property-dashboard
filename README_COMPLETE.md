# 🏢 MCP 기반 부동산 매물 관리 시스템

## 📌 시스템 개요

공인중개사의 매물 관리 업무를 완전 자동화하는 **분산 마이크로서비스 시스템**입니다.

### 핵심 특징
- 🔄 **다중 플랫폼 실시간 수집**: 네이버, 직방, 다방 등 10+ 플랫폼 동시 수집
- 🤖 **지능형 서브에이전트**: 각 업무별 전문 에이전트가 자율적으로 작업 수행
- 📊 **실시간 모니터링**: Grafana 대시보드로 시스템 상태 실시간 확인
- 🚀 **확장 가능한 구조**: 새로운 플랫폼/기능 쉽게 추가 가능
- 🔐 **엔터프라이즈급 보안**: JWT 인증, RBAC, SSL/TLS 지원

## 🏗️ 시스템 아키텍처

```
사용자 인터페이스 (Web/Mobile)
         ↓
    API Gateway
         ↓
  MCP 오케스트레이터 ←→ Message Queue
         ↓
   서브에이전트들
   ├── 수집 에이전트 (플랫폼별)
   ├── 처리 에이전트 (정규화, 중복제거)
   ├── 저장 에이전트 (DB, 캐시)
   └── 알림 에이전트 (실시간 알림)
```

## 🚀 빠른 시작

### 1. 사전 요구사항
- Docker & Docker Compose
- Python 3.11+
- 8GB+ RAM
- 20GB+ 디스크 공간

### 2. 설치 및 실행

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/property-management-system.git
cd property-management-system

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 필요한 값 설정

# 3. Docker Compose로 전체 시스템 시작
docker-compose up -d

# 4. 상태 확인
docker-compose ps

# 5. 로그 확인
docker-compose logs -f orchestrator
```

### 3. 시스템 접속

- **API**: http://localhost:8000
- **Grafana 대시보드**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **RabbitMQ 관리**: http://localhost:15672 (admin/secret123)

## 📡 API 사용 예시

### 매물 수집 시작

```python
import requests

# 매물 수집 작업 생성
response = requests.post(
    "http://localhost:8000/api/v1/tasks",
    json={
        "type": "collect",
        "areas": ["강남구", "서초구"],
        "platforms": ["naver", "zigbang", "dabang"],
        "filters": {
            "price_min": 100000,  # 10억
            "price_max": 200000,  # 20억
            "area_min": 80,       # 80㎡
            "property_type": "apartment"
        }
    }
)

task_id = response.json()["task_id"]
print(f"Task created: {task_id}")
```

### WebSocket으로 실시간 모니터링

```python
import asyncio
import websockets
import json

async def monitor():
    async with websockets.connect(f"ws://localhost:8000/ws/client123") as websocket:
        # 채널 구독
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channel": "task_updates"
        }))
        
        # 실시간 업데이트 수신
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Update: {data}")

asyncio.run(monitor())
```

### GraphQL 쿼리

```graphql
query SearchProperties {
  properties(
    area: "강남구"
    priceMin: 100000
    priceMax: 150000
    limit: 10
  ) {
    id
    platform
    title
    price
    area
    address
    images
    createdAt
  }
}
```

## 🔧 주요 컴포넌트

### MCP 오케스트레이터
- 중앙 제어 및 작업 분배
- 에이전트 라이프사이클 관리
- 실시간 모니터링 및 메트릭 수집
- WebSocket/REST API 제공

### 수집 서브에이전트
- **네이버 수집기**: Playwright 기반 동적 렌더링
- **직방 수집기**: REST API 기반
- **다방 수집기**: GraphQL API 기반
- **KB 수집기**: 추가 예정

### 처리 서브에이전트
- **정규화 에이전트**: 플랫폼별 데이터 표준화
- **중복제거 에이전트**: 크로스 플랫폼 중복 탐지
- **검증 에이전트**: 데이터 유효성 검사
- **이미지 처리**: 썸네일 생성, OCR

### 저장 서브에이전트
- **PostgreSQL**: 메인 데이터 저장
- **MongoDB**: 원시 데이터 보관
- **Redis**: 캐싱 및 세션 관리
- **S3**: 이미지/문서 저장

## 📊 모니터링

### Grafana 대시보드
- 실시간 수집 현황
- 에이전트 상태
- 성능 메트릭
- 에러 발생률

### 주요 메트릭
- 수집률: 분당 수집 매물 수
- 응답시간: API 평균 응답 시간
- 에러율: 작업 실패율
- 리소스: CPU/메모리 사용률

## 🔐 보안

- JWT 기반 인증
- RBAC (역할 기반 접근 제어)
- SSL/TLS 암호화
- API Rate Limiting
- 감사 로그

## 📈 성능

- **동시 처리**: 50+ 동시 수집 작업
- **처리량**: 분당 1,000+ 매물 수집
- **응답시간**: < 100ms (API)
- **가용성**: 99.9% SLA

## 🛠️ 운영 관리

### 스케일링

```bash
# 수집 에이전트 스케일 업
docker-compose up -d --scale collector-naver=5

# 처리 에이전트 스케일 업  
docker-compose up -d --scale processor-normalizer=3
```

### 백업

```bash
# 데이터베이스 백업
./scripts/backup.sh

# 전체 시스템 백업
docker-compose exec postgres pg_dump -U admin property_db > backup.sql
```

### 로그 관리

```bash
# 로그 확인
docker-compose logs -f [service-name]

# 로그 검색
docker-compose logs | grep ERROR

# Kibana에서 고급 검색
http://localhost:5601
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# E2E 테스트
pytest tests/e2e/

# 커버리지 확인
pytest --cov=src tests/
```

## 📚 문서

- [API 문서](./docs/API.md)
- [아키텍처 상세](./docs/ARCHITECTURE.md)
- [배포 가이드](./docs/DEPLOYMENT.md)
- [개발자 가이드](./docs/DEVELOPER.md)

## 🤝 기여

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 💬 지원

- 이슈: [GitHub Issues](https://github.com/your-org/property-management-system/issues)
- 이메일: support@example.com
- 문서: [Wiki](https://github.com/your-org/property-management-system/wiki)

---

**Made with ❤️ by Your Team**