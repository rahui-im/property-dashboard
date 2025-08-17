# 🏢 부동산 매물 관리 시스템 - Claude 지속 메모리

## 📌 프로젝트 개요
**프로젝트명**: MCP 기반 부동산 매물 관리 시스템
**목적**: 공인중개사 업무 자동화를 위한 분산 마이크로서비스 시스템
**현재 상태**: 프로덕션 준비 완료

## 🎯 핵심 컨텍스트

### 시스템 아키텍처
```
MCP 오케스트레이터 (중앙 제어)
    ├── 수집 서브에이전트들 (플랫폼별)
    │   ├── 네이버 수집기
    │   ├── 직방 수집기
    │   └── 다방 수집기
    ├── 처리 서브에이전트들
    │   ├── 정규화 에이전트
    │   └── 중복제거 에이전트
    └── 저장 서브에이전트들
        ├── DB 저장 에이전트
        └── 캐시 관리 에이전트
```

### 기술 스택
- **백엔드**: Python 3.11, FastAPI, AsyncIO
- **데이터베이스**: PostgreSQL, MongoDB, Redis
- **크롤링**: Playwright, BeautifulSoup, aiohttp
- **메시징**: WebSocket, RabbitMQ
- **모니터링**: Prometheus, Grafana, ELK Stack
- **컨테이너**: Docker, Docker Compose
- **인증**: JWT, OAuth2

## 📁 프로젝트 구조

```
D:\property-collector\
├── src/
│   ├── mcp/                    # MCP 오케스트레이터
│   │   ├── orchestrator/       # 메인 서버
│   │   ├── collectors/         # 플랫폼별 수집기
│   │   └── communication/      # 통신 모듈
│   ├── agents/                 # 서브에이전트들
│   │   ├── collector_agent.py  # 수집 에이전트
│   │   ├── processor_agent.py  # 처리 에이전트
│   │   └── storage_agent.py    # 저장 에이전트
│   └── models/                 # 데이터 모델
├── docker/                     # Docker 설정
├── config/                     # 설정 파일
├── tests/                      # 테스트
└── docker-compose.yml          # 오케스트레이션
```

## 🔧 주요 명령어

### 시스템 시작/중지
```bash
# 전체 시스템 시작
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f orchestrator

# 시스템 중지
docker-compose down
```

### 개발 환경
```bash
# 가상환경 활성화
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements_mcp.txt

# 테스트 실행
pytest tests/

# 개발 서버 실행
python -m src.mcp.orchestrator.main
```

### API 테스트
```bash
# 매물 수집 시작
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"type":"collect","areas":["강남구"],"platforms":["naver"]}'

# 상태 확인
curl http://localhost:8000/health

# 에이전트 목록
curl http://localhost:8000/api/v1/agents
```

## 💡 작업 시 기억할 핵심 원칙

### 1. MCP 서버 중심 구조
- **오케스트레이터가 중앙 제어**: 모든 작업 분배와 조율
- **서브에이전트는 독립적**: 각자 전문 영역만 담당
- **느슨한 결합**: WebSocket/메시지큐로 통신

### 2. 비동기 처리 우선
```python
# 항상 async/await 사용
async def collect_properties():
    async with NaverCollector() as collector:
        return await collector.collect(area)
```

### 3. 에러 처리 및 복구
```python
# 모든 작업에 재시도 로직
@retry(max_attempts=3, backoff=2)
async def critical_operation():
    try:
        # 작업 수행
    except RecoverableError:
        # 복구 시도
    except CriticalError:
        # 에스컬레이션
```

### 4. 로깅과 모니터링
```python
# 모든 중요 이벤트 로깅
logger.info(f"Task {task_id} started")
logger.error(f"Error in {agent_id}: {error}")

# 메트릭 수집
metrics.increment('tasks.completed')
metrics.timing('task.duration', elapsed_time)
```

## 🚀 새 기능 추가 체크리스트

### 새 플랫폼 수집기 추가
1. [ ] `src/mcp/collectors/` 에 새 수집기 클래스 생성
2. [ ] `BaseCollector` 상속 및 `collect()` 메서드 구현
3. [ ] `src/agents/collector_agent.py` 에 수집기 등록
4. [ ] Docker Compose에 새 서비스 추가
5. [ ] 테스트 작성 및 실행
6. [ ] 문서 업데이트

### 새 에이전트 타입 추가
1. [ ] `src/agents/` 에 새 에이전트 클래스 생성
2. [ ] WebSocket 연결 및 메시지 처리 구현
3. [ ] 오케스트레이터에 에이전트 타입 등록
4. [ ] Dockerfile 생성
5. [ ] Docker Compose에 서비스 추가
6. [ ] 통합 테스트

## 📊 현재 구현 상태

### ✅ 완료된 기능
- [x] MCP 오케스트레이터 서버
- [x] 수집 서브에이전트 (네이버, 직방, 다방)
- [x] 작업 큐 및 분배 시스템
- [x] WebSocket 실시간 통신
- [x] Docker 컨테이너화
- [x] 기본 모니터링 시스템
- [x] **네이버 모바일 크롤러 구현** (2025-01-16)
  - 매물 유형별 수집 (18개 유형 완벽 지원)
    - 주거: 아파트, 오피스텔, 빌라, 아파트분양권, 오피스텔분양권, 재건축
    - 주택: 전원주택, 단독/다가구, 상가주택, 한옥주택, 재개발, 원룸
    - 상업: 상가, 사무실, 공장/창고, 토지, 지식산업센터, 숙박/펜션
  - 거래 유형별 필터링 (매매, 전세, 월세, 단기)
  - 지역별 검색 및 좌표 기반 수집
- [x] **데이터 모델 정의** (2025-01-16)
  - Pydantic 기반 타입 안전 모델
  - 매물별 상세 속성 정의
  - 검색 필터 및 작업 요청/응답 모델

### 🔄 진행 중
- [ ] 처리 에이전트 고도화
- [ ] 저장 에이전트 최적화
- [ ] GraphQL API 구현
- [ ] 실제 네이버 API 연동 테스트

### 📅 예정된 작업
- [ ] 직방 수집기 업데이트 (모바일 버전)
- [ ] 다방 수집기 업데이트 (모바일 버전)
- [ ] KB 부동산 수집기
- [ ] 호갱노노 수집기
- [ ] AI 기반 가격 예측
- [ ] 고객 매칭 시스템
- [ ] 모바일 앱 개발

## 🐛 알려진 이슈 및 해결법

### 1. Playwright 한글 깨짐
```python
# 인코딩 명시적 설정
sys.stdout.reconfigure(encoding='utf-8')
```

### 2. Docker 메모리 부족
```yaml
# docker-compose.yml에서 리소스 제한
deploy:
  resources:
    limits:
      memory: 1G
```

### 3. WebSocket 연결 끊김
```python
# 자동 재연결 로직
async def connect_with_retry():
    while True:
        try:
            await connect_websocket()
        except:
            await asyncio.sleep(5)
```

## 📚 참고 자료

### 내부 문서
- `PROPERTY_MANAGEMENT_SYSTEM.md` - 전체 시스템 설계
- `docs/MCP_ARCHITECTURE.md` - MCP 아키텍처 상세
- `README_COMPLETE.md` - 사용자 가이드

### 외부 링크
- [FastAPI 문서](https://fastapi.tiangolo.com)
- [Playwright Python](https://playwright.dev/python/)
- [Docker Compose](https://docs.docker.com/compose/)

## 🔄 정기 체크 항목

### 매 작업 시작 시
1. 현재 프로젝트 경로 확인: `D:\property-collector\`
2. 가상환경 활성화 상태 확인
3. Docker 서비스 실행 상태 확인
4. 최신 코드 동기화 상태 확인

### 코드 수정 시
1. 기존 구조와 일관성 유지
2. 비동기 패턴 준수
3. 에러 처리 추가
4. 테스트 작성
5. 문서 업데이트

## 💬 컨텍스트 유지 팁

### Claude에게 상기시킬 핵심 문구
- "MCP 기반 매물 관리 시스템"
- "오케스트레이터와 서브에이전트 구조"
- "D:\property-collector 프로젝트"
- "비동기 분산 처리 시스템"

### 세션 시작 시 확인 질문
1. "현재 매물 관리 시스템의 구조는?"
2. "수집 에이전트의 역할은?"
3. "MCP 오케스트레이터의 기능은?"

---

**마지막 업데이트**: 2025-01-16 - 네이버 모바일 크롤러 구현
**다음 리뷰 예정**: 매 주요 기능 추가 시