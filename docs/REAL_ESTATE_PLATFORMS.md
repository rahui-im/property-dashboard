# 🏢 부동산 플랫폼 연결 가이드

## 📌 연결 가능한 부동산 사이트 목록

### 1. 🟢 현재 연결된 플랫폼 (실시간 데이터 수집 가능)

#### 네이버 부동산 (Naver Real Estate)
- **URL**: https://land.naver.com
- **특징**: 국내 최대 부동산 플랫폼
- **매물 종류**: 아파트, 오피스텔, 빌라, 원룸, 상가, 토지 등 전체
- **API**: REST API (공개)
- **실시간 데이터**: ✅ 가능
- **구현 상태**: ✅ 완료

#### 직방 (Zigbang)
- **URL**: https://www.zigbang.com
- **특징**: 원룸, 오피스텔 전문 플랫폼
- **매물 종류**: 원룸, 투룸, 오피스텔, 아파트
- **API**: REST API (공개)
- **실시간 데이터**: ✅ 가능
- **구현 상태**: ✅ 완료

### 2. 🟡 추가 연결 가능한 플랫폼 (API 제공)

#### 다방 (Dabang)
- **URL**: https://www.dabangapp.com
- **특징**: 원룸, 오피스텔 중개 앱
- **매물 종류**: 원룸, 투룸, 쓰리룸, 오피스텔
- **API**: REST API (제한적 공개)
- **실시간 데이터**: ✅ 가능
- **구현 상태**: 🔄 부분 구현

#### KB부동산 (KB Real Estate)
- **URL**: https://kbland.kr
- **특징**: KB국민은행 부동산 서비스
- **매물 종류**: 아파트, 주택, 토지, 상가
- **API**: Liiv ON API
- **실시간 데이터**: ✅ 가능
- **구현 상태**: 🔄 부분 구현

#### 피터팬의 좋은방 구하기 (Peterpan)
- **URL**: https://www.peterpanz.com
- **특징**: 셰어하우스, 원룸 전문
- **매물 종류**: 셰어하우스, 원룸, 고시원
- **API**: REST API
- **실시간 데이터**: ✅ 가능
- **구현 상태**: 🔄 부분 구현

#### 호갱노노 (Hogangnono)
- **URL**: https://hogangnono.com
- **특징**: 실거래가 정보, 시세 분석
- **매물 종류**: 아파트 실거래가
- **API**: 공공데이터 기반
- **실시간 데이터**: ⚠️ 제한적 (실거래가는 지연)
- **구현 상태**: ❌ 미구현

### 3. 🔴 크롤링 필요 플랫폼 (API 미제공)

#### 부동산114 (R114)
- **URL**: https://www.r114.com
- **특징**: 종합 부동산 정보
- **매물 종류**: 전체
- **API**: ❌ 미제공
- **크롤링**: Playwright 필요
- **구현 상태**: ❌ 미구현

#### 스피드뱅크 (Speedbank)
- **URL**: https://www.speedbank.co.kr
- **특징**: 급매물 전문
- **매물 종류**: 급매 아파트, 빌라
- **API**: ❌ 미제공
- **크롤링**: 필요
- **구현 상태**: 🔄 Mock 데이터로 구현

#### 부동산뱅크 (REBank)
- **URL**: https://www.rebank.co.kr
- **특징**: 경매, 공매 정보
- **매물 종류**: 경매, 공매 물건
- **API**: ❌ 미제공
- **크롤링**: 필요
- **구현 상태**: ❌ 미구현

### 4. 🌐 공공 데이터 플랫폼

#### 국토교통부 실거래가 공개시스템
- **URL**: http://rt.molit.go.kr
- **특징**: 실거래가 공식 데이터
- **데이터**: 아파트, 주택, 토지 실거래가
- **API**: 공공데이터포털 API
- **실시간 데이터**: ⚠️ 1-2개월 지연
- **구현 상태**: ❌ 미구현

#### 한국부동산원 (R-ONE)
- **URL**: https://www.reb.or.kr
- **특징**: 부동산 통계, 시세
- **데이터**: 시세, 통계, 분석 자료
- **API**: 일부 제공
- **실시간 데이터**: ⚠️ 제한적
- **구현 상태**: ❌ 미구현

## 📊 플랫폼별 데이터 수집 방식

### API 직접 연결 (가장 안정적)
```javascript
// 네이버 부동산 예시
const response = await fetch('https://m.land.naver.com/cluster/ajax/articleList');
const data = await response.json();
```

### 웹 크롤링 (API 없는 경우)
```javascript
// Playwright 사용 예시
const browser = await playwright.chromium.launch();
const page = await browser.newPage();
await page.goto('https://www.r114.com');
const data = await page.evaluate(() => {
  // DOM에서 데이터 추출
});
```

### 공공 API 활용
```javascript
// 국토교통부 실거래가 API
const response = await fetch('http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev');
```

## 🔧 구현 우선순위

### 1단계 (완료)
- ✅ 네이버 부동산
- ✅ 직방

### 2단계 (진행중)
- 🔄 다방
- 🔄 KB부동산
- 🔄 피터팬의 좋은방 구하기

### 3단계 (예정)
- ⏳ 호갱노노
- ⏳ 국토교통부 실거래가
- ⏳ 부동산114

### 4단계 (검토중)
- ⏳ 스피드뱅크
- ⏳ 부동산뱅크
- ⏳ 한국부동산원

## 💡 통합 검색 기능

현재 구현된 통합 검색 API는 다음과 같이 작동합니다:

1. **주소 입력**: "삼성동 151-7" 같은 주소 입력
2. **플랫폼 선택**: 전체 또는 특정 플랫폼 선택
3. **실시간 검색**: 각 플랫폼 API 병렬 호출
4. **결과 통합**: 모든 플랫폼 결과 병합
5. **중복 제거**: 동일 매물 필터링
6. **통계 제공**: 가격, 면적, 매물 수 등 분석

## 🚀 사용 방법

### 웹 인터페이스
1. https://your-app.vercel.app 접속
2. 주소 입력 (예: "삼성동 151-7")
3. 검색 버튼 클릭
4. 각 플랫폼별 매물 확인

### API 직접 호출
```bash
# 모든 플랫폼 검색
GET /api/realtime-search?address=삼성동 151-7&platforms=all

# 특정 플랫폼만 검색
GET /api/realtime-search?address=삼성동 151-7&platforms=naver,zigbang
```

## 📝 주의사항

1. **API 제한**: 각 플랫폼별 Rate Limit 존재
2. **법적 문제**: 상업적 사용 시 각 플랫폼 약관 확인 필요
3. **데이터 정확성**: 실시간 데이터와 실제 매물 간 차이 발생 가능
4. **개인정보**: 수집된 데이터의 개인정보 처리 주의

## 🔄 업데이트 계획

- 매주 새로운 플랫폼 1-2개 추가
- 기존 플랫폼 API 안정성 개선
- 데이터 정확도 향상
- 캐싱 및 성능 최적화

---

**마지막 업데이트**: 2024-01-15
**문의**: GitHub Issues에서 요청 및 버그 신고