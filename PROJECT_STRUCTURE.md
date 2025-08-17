# 📁 프로젝트 구조

## 디렉토리 구조
```
property-collector/
│
├── 📂 frontend/              # Next.js 웹 애플리케이션
│   ├── components/           # React 컴포넌트
│   ├── pages/               # Next.js 페이지
│   ├── public/              # 정적 파일
│   ├── styles/              # CSS 스타일
│   ├── package.json         # Node.js 의존성
│   └── next.config.js       # Next.js 설정
│
├── 📂 src/                  # 백엔드 소스 코드
│   ├── mcp/                # MCP 오케스트레이터
│   │   ├── orchestrator/   # 메인 서버
│   │   ├── collectors/     # 플랫폼별 수집기
│   │   └── agents/         # 에이전트
│   ├── models/             # 데이터 모델
│   └── processors/         # 데이터 처리
│
├── 📂 scripts/              # 실행 스크립트
│   ├── collectors/         # 데이터 수집 스크립트
│   │   ├── collect_samsung1dong.py
│   │   ├── naver_collector.py
│   │   ├── zigbang_collector.py
│   │   └── ...
│   ├── processors/         # 데이터 처리 스크립트
│   │   ├── data_integration_system.py
│   │   ├── convert_to_static.py
│   │   └── ...
│   ├── tests/             # 테스트 스크립트
│   │   ├── test_collectors.py
│   │   └── address_search_test.py
│   └── batch/             # 배치 실행 파일
│       └── run.bat
│
├── 📂 data/                # 데이터 저장소
│   ├── raw/               # 원본 수집 데이터 (JSON)
│   ├── processed/         # 처리된 데이터
│   ├── reports/           # HTML 리포트
│   └── screenshots/       # 스크린샷
│
├── 📂 docs/                # 문서
│   ├── PRD_부동산매물시스템.md
│   ├── MCP_ARCHITECTURE.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── ...
│
├── 📂 docker/              # Docker 설정
│   ├── Dockerfile.collector
│   └── Dockerfile.orchestrator
│
├── 📂 config/              # 설정 파일
│   └── mcp_config.yaml
│
├── 📂 tests/               # 통합 테스트
│
├── 📂 logs/                # 로그 파일
│
├── 📂 venv/                # Python 가상환경
│
├── 📂 node_modules/        # Node.js 패키지
│
├── 📜 README.md            # 프로젝트 소개
├── 📜 CLAUDE.md            # Claude 지속 메모리
├── 📜 requirements.txt     # Python 의존성
├── 📜 docker-compose.yml   # Docker Compose 설정
└── 📜 .gitignore          # Git 제외 파일
```

## 각 디렉토리 설명

### `/frontend`
- **용도**: 사용자 인터페이스 (Next.js 대시보드)
- **주요 파일**: Dashboard.js, index.js
- **배포**: Vercel로 배포

### `/src`
- **용도**: 백엔드 핵심 로직
- **구조**: MCP 아키텍처 기반
- **실행**: Docker 컨테이너로 운영

### `/scripts`
- **용도**: 독립 실행 가능한 스크립트
- **분류**: 수집/처리/테스트별 구분
- **실행 방법**: `python scripts/collectors/collect_samsung1dong.py`

### `/data`
- **용도**: 모든 데이터 파일 저장
- **raw**: 원본 JSON 데이터
- **processed**: 정제된 데이터
- **reports**: HTML 보고서

### `/docs`
- **용도**: 프로젝트 문서
- **내용**: 설계서, 가이드, 매뉴얼

## 파일 명명 규칙

### Python 파일
- 수집기: `{platform}_collector.py`
- 처리기: `{process}_processor.py`
- 테스트: `test_{feature}.py`

### 데이터 파일
- 원본: `{platform}_{area}_{timestamp}.json`
- 리포트: `{area}_report_{timestamp}.html`

## 실행 순서

1. **데이터 수집**
   ```bash
   python scripts/collectors/multi_platform_collector.py
   ```

2. **데이터 통합**
   ```bash
   python scripts/processors/data_integration_system.py
   ```

3. **정적 파일 생성**
   ```bash
   python scripts/processors/convert_to_static.py
   ```

4. **웹 서버 실행**
   ```bash
   cd frontend && npm run dev
   ```

## Git 브랜치 전략

- `main`: 프로덕션 배포
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발
- `hotfix/*`: 긴급 수정