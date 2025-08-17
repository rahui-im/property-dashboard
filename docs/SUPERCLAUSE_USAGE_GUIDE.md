# 🏢 부동산 매물 시스템 + SuperClaude 활용 가이드

## 📌 프로젝트 현황
- **현재 상태**: MCP 오케스트레이터 기본 구현 완료
- **다음 목표**: 실제 매물 수집 및 프로덕션 배포
- **주요 과제**: 크롤러 고도화, 성능 최적화, 실시간 알림

---

## 🚀 즉시 활용 가능한 시나리오

### 1️⃣ 현재 시스템 전체 점검 (5분)

```bash
# 전체 시스템 분석
/analyze --comprehensive

예상 결과:
📊 프로젝트 분석 결과:
  - 구조: MCP 기반 마이크로서비스 ✅
  - 수집기: 네이버, 직방, 다방 (기본 구현)
  - 문제점:
    ⚠️ 실제 크롤링 로직 미구현 (테스트 데이터만)
    ⚠️ 에러 복구 로직 부족
    ⚠️ 테스트 커버리지 0%
    ⚠️ 프로덕션 배포 설정 미비

💡 개선 제안:
  1. 실제 크롤러 구현 필요
  2. 레이트 리미팅 강화
  3. 테스트 추가
  4. 모니터링 시스템 구축
```

### 2️⃣ 네이버 크롤러 실제 구현 (20분 → 5분)

```bash
# 네이버 실제 크롤러 구현
/implement naver-real-crawler --playwright --anti-bot

SuperClaude가 자동으로:
```

```python
# src/mcp/collectors/naver_real.py
class NaverRealCollector(BaseCollector):
    """실제 네이버 부동산 크롤러"""
    
    async def collect(self, area: str):
        async with async_playwright() as p:
            # 봇 탐지 회피 설정
            browser = await p.chromium.launch(
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_real_user_agent(),
                locale='ko-KR'
            )
            
            # 쿠키 및 세션 관리
            await context.add_cookies(self._load_cookies())
            
            page = await context.new_page()
            
            # 스텔스 모드 적용
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # 실제 크롤링 로직
            properties = []
            
            # 1. 지역 검색
            await page.goto(f"{self.base_url}/article")
            await page.wait_for_selector('.filter_btn_select')
            
            # 2. 필터 설정
            await self._apply_filters(page, area)
            
            # 3. 무한 스크롤 처리
            while len(properties) < self.max_items:
                # 현재 페이지 아이템 수집
                items = await page.query_selector_all('.item_inner')
                
                for item in items:
                    property_data = await self._extract_property(item)
                    properties.append(property_data)
                
                # 스크롤 로딩
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)
                
                # 더 이상 로드할 항목이 없으면 종료
                if not await self._has_more_items(page):
                    break
                    
            return properties
            
    async def _extract_property(self, element):
        """실제 데이터 추출"""
        return {
            'id': await element.get_attribute('data-article-no'),
            'title': await element.query_selector('.item_title').inner_text(),
            'price': self._parse_price(
                await element.query_selector('.price').inner_text()
            ),
            'area': self._parse_area(
                await element.query_selector('.specs').inner_text()
            ),
            'floor': await element.query_selector('.floor').inner_text(),
            'address': await element.query_selector('.address').inner_text(),
            'agent': await element.query_selector('.agent_name').inner_text(),
            'images': await self._extract_images(element),
            'description': await element.query_selector('.desc').inner_text()
        }
```

### 3️⃣ 캡차 및 봇 탐지 우회 (30분 → 5분)

```bash
/implement anti-detection --advanced

SuperClaude 구현:
```

```python
# src/mcp/collectors/anti_detection.py
class AntiDetectionMixin:
    """봇 탐지 우회 기능"""
    
    async def setup_stealth_browser(self):
        """스텔스 브라우저 설정"""
        playwright = await async_playwright().start()
        
        # 1. 실제 Chrome 실행 파일 사용
        browser = await playwright.chromium.launch(
            executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized'
            ]
        )
        
        # 2. 지문 위조
        await self._spoof_fingerprint(browser)
        
        # 3. WebRTC 누출 방지
        await self._block_webrtc_leak(browser)
        
        return browser
        
    async def handle_captcha(self, page):
        """캡차 자동 처리"""
        # reCAPTCHA v2 감지
        if await page.query_selector('iframe[src*="recaptcha"]'):
            # 2captcha API 사용
            solver = TwoCaptcha(api_key=os.getenv('CAPTCHA_API_KEY'))
            
            # 캡차 이미지 캡처
            captcha_element = await page.query_selector('.g-recaptcha')
            screenshot = await captcha_element.screenshot()
            
            # 캡차 해결
            result = await solver.solve_recaptcha(
                sitekey=await page.evaluate('grecaptcha.getSiteKey()'),
                url=page.url
            )
            
            # 결과 입력
            await page.evaluate(f'grecaptcha.callback("{result}")')
            
    async def rotate_proxy(self):
        """프록시 로테이션"""
        proxy = random.choice(self.proxy_pool)
        return {
            'server': f'http://{proxy["ip"]}:{proxy["port"]}',
            'username': proxy['username'],
            'password': proxy['password']
        }
```

### 4️⃣ 실시간 가격 변동 추적 (1시간 → 10분)

```bash
/implement price-tracker --realtime --alert

SuperClaude 구현:
```

```python
# src/services/price_tracker.py
class PriceTracker:
    """실시간 가격 추적 서비스"""
    
    def __init__(self):
        self.redis = aioredis.from_url("redis://localhost")
        self.db = Database()
        self.notifier = NotificationService()
        
    async def track_price_changes(self):
        """가격 변동 추적"""
        while True:
            # 1. 현재 매물 수집
            current_properties = await self.collect_current_prices()
            
            # 2. 이전 가격과 비교
            for prop in current_properties:
                cached_price = await self.redis.get(f"price:{prop['id']}")
                
                if cached_price:
                    old_price = int(cached_price)
                    new_price = prop['price']
                    
                    # 가격 변동 감지
                    if old_price != new_price:
                        change_percent = ((new_price - old_price) / old_price) * 100
                        
                        # 3. 변동 이력 저장
                        await self.save_price_history(prop['id'], old_price, new_price)
                        
                        # 4. 알림 조건 체크
                        if abs(change_percent) >= 5:  # 5% 이상 변동
                            await self.send_alert(prop, change_percent)
                            
                # 캐시 업데이트
                await self.redis.set(f"price:{prop['id']}", new_price, ex=3600)
                
            # 5분마다 체크
            await asyncio.sleep(300)
            
    async def send_alert(self, property_data, change_percent):
        """가격 변동 알림"""
        message = f"""
        🏠 매물 가격 변동 알림
        
        물건: {property_data['title']}
        주소: {property_data['address']}
        
        변동: {change_percent:+.1f}%
        이전: {property_data['old_price']:,}만원
        현재: {property_data['price']:,}만원
        
        바로가기: {property_data['url']}
        """
        
        # 관심 고객에게 알림
        interested_users = await self.get_interested_users(property_data)
        for user in interested_users:
            await self.notifier.send(user, message)
```

### 5️⃣ 중복 매물 지능형 탐지 (40분 → 5분)

```bash
/implement duplicate-detector --ai-powered

SuperClaude 구현:
```

```python
# src/services/duplicate_detector.py
class IntelligentDuplicateDetector:
    """AI 기반 중복 탐지"""
    
    async def detect_duplicates(self, new_property):
        """중복 매물 탐지"""
        # 1. 기본 정보로 후보 찾기
        candidates = await self.find_candidates(new_property)
        
        duplicates = []
        for candidate in candidates:
            similarity = self.calculate_similarity(new_property, candidate)
            
            if similarity > 0.85:  # 85% 이상 유사
                duplicates.append({
                    'property': candidate,
                    'similarity': similarity,
                    'reason': self.get_duplicate_reason(new_property, candidate)
                })
                
        return duplicates
        
    def calculate_similarity(self, prop1, prop2):
        """유사도 계산"""
        score = 0.0
        
        # 1. 주소 유사도 (40%)
        address_sim = fuzz.ratio(prop1['address'], prop2['address']) / 100
        score += address_sim * 0.4
        
        # 2. 면적 유사도 (20%)
        if abs(prop1['area'] - prop2['area']) < 5:  # 5㎡ 이내
            score += 0.2
            
        # 3. 가격 유사도 (20%)
        price_diff = abs(prop1['price'] - prop2['price']) / prop1['price']
        if price_diff < 0.05:  # 5% 이내
            score += 0.2
            
        # 4. 이미지 유사도 (20%)
        if self.images_similar(prop1['images'], prop2['images']):
            score += 0.2
            
        return score
        
    def images_similar(self, images1, images2):
        """이미지 유사도 검사"""
        # 딥러닝 모델로 이미지 비교
        for img1 in images1[:3]:  # 대표 이미지 3개
            for img2 in images2[:3]:
                similarity = self.compare_images_with_ai(img1, img2)
                if similarity > 0.9:
                    return True
        return False
```

### 6️⃣ 성능 최적화 및 스케일링 (2시간 → 15분)

```bash
/analyze --focus performance
/improve --performance --scale

SuperClaude 최적화:
```

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # 로드 밸런서
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - orchestrator1
      - orchestrator2
      - orchestrator3

  # 오케스트레이터 클러스터 (3개)
  orchestrator1:
    build: .
    environment:
      - INSTANCE_ID=1
      - REDIS_CLUSTER=true
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
          
  # 수집기 풀 (자동 스케일링)
  collector-naver:
    build: .
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
      restart_policy:
        condition: on-failure
        
  # 메시지 큐 클러스터
  rabbitmq:
    image: rabbitmq:3-management
    environment:
      - RABBITMQ_ERLANG_COOKIE=secret
      - RABBITMQ_USE_CLUSTER=true
    deploy:
      replicas: 3
```

### 7️⃣ 프로덕션 배포 준비 (3시간 → 20분)

```bash
/build --production --test --deploy

SuperClaude 자동 실행:
```

```bash
✅ 프로덕션 체크리스트:

1. 환경 변수 검증
   - DB 연결 ✅
   - Redis 연결 ✅
   - API 키 설정 ✅

2. 보안 검사
   - SQL Injection 방어 ✅
   - XSS 방어 ✅
   - Rate Limiting ✅
   - HTTPS 설정 ✅

3. 성능 테스트
   - 부하 테스트: 1000 req/s ✅
   - 응답 시간: <100ms ✅
   - 메모리 사용: <500MB ✅

4. 모니터링 설정
   - Prometheus ✅
   - Grafana 대시보드 ✅
   - 알림 설정 ✅

5. 백업 및 복구
   - DB 백업 스크립트 ✅
   - 롤백 계획 ✅

6. 배포
   - Docker 이미지 빌드 ✅
   - Kubernetes 매니페스트 ✅
   - CI/CD 파이프라인 ✅
```

---

## 📊 일일 운영 시나리오

### 오전 9시 - 시스템 점검
```bash
# 전체 상태 확인
/analyze --health-check

# 야간 수집 결과 확인
/analyze logs/night-collection.log
```

### 오전 10시 - 새 기능 개발
```bash
# 카카오 알림 기능 추가
/implement kakao-notification --api

# 테스트
/test notification --integration
```

### 오후 2시 - 성능 이슈 대응
```bash
# 느려진 API 분석
/troubleshoot "API 응답이 2초 걸려요"

# 즉시 최적화
/improve --performance --urgent
```

### 오후 4시 - 고객 요청 처리
```bash
# 새로운 지역 추가
/implement area-expansion --area "판교"

# 문서 업데이트
/document --update README.md
```

### 오후 6시 - 배포 준비
```bash
# 전체 테스트
/test --all --coverage

# 스테이징 배포
/build --staging --deploy
```

---

## 💡 프로젝트 특화 커스텀 명령어

```bash
# 매물 수집 시작
/collect --area "강남구" --platform all

# 가격 분석
/analyze-prices --trend --area "강남구"

# 중복 제거
/cleanup-duplicates --aggressive

# 일일 리포트
/report --daily --email admin@example.com

# 긴급 수집
/collect --urgent --priority "강남 아파트"
```

---

## 🎯 향후 로드맵 with SuperClaude

### Phase 1 (1주일)
```bash
/implement real-crawlers --all-platforms
/test crawlers --comprehensive
/document crawlers
```

### Phase 2 (2주일)
```bash
/implement customer-matching --ai
/implement price-prediction --ml
/test ai-features
```

### Phase 3 (3주일)
```bash
/implement mobile-app --react-native
/implement admin-dashboard --react
/deploy --production
```

---

**이렇게 SuperClaude를 활용하면 개발 속도가 10배 이상 빨라집니다!** 🚀