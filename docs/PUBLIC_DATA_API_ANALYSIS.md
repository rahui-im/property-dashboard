# 🏢 공공데이터포털 부동산 API 분석 및 통합 계획

## 📊 1. 핵심 공공데이터 API 목록

### 1.1 국토교통부 실거래가 APIs

#### 🏠 아파트 매매 실거래가
- **API 명**: 국토교통부_아파트매매 실거래 상세 자료
- **엔드포인트**: `http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev`
- **주요 데이터**:
  - 거래금액, 거래일자
  - 전용면적, 층 정보
  - 아파트명, 법정동
  - 건축년도
- **활용도**: ⭐⭐⭐⭐⭐ (필수)

#### 🏠 아파트 전월세 실거래가
- **API 명**: 국토교통부_아파트 전월세 자료
- **엔드포인트**: `http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent`
- **주요 데이터**:
  - 보증금액, 월세금액
  - 계약기간
  - 전용면적, 층 정보
- **활용도**: ⭐⭐⭐⭐⭐ (필수)

#### 🏢 오피스텔 매매 실거래가
- **API 명**: 국토교통부_오피스텔 매매 신고 자료
- **엔드포인트**: `http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiTrade`
- **활용도**: ⭐⭐⭐⭐

#### 🏢 오피스텔 전월세 실거래가
- **API 명**: 국토교통부_오피스텔 전월세 신고 자료
- **엔드포인트**: `http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiRent`
- **활용도**: ⭐⭐⭐⭐

### 1.2 한국부동산원 APIs

#### 📈 아파트 실거래가격지수
- **API 명**: 한국부동산원_아파트 실거래가격지수
- **용도**: 시세 변동 추이 분석
- **활용도**: ⭐⭐⭐

#### 📊 전월세 전환율
- **API 명**: 한국부동산원_전월세전환율
- **용도**: 전세/월세 가격 비교 분석
- **활용도**: ⭐⭐⭐

### 1.3 추가 유용한 APIs

#### 🏗️ 건축물대장 정보
- **API 명**: 국토교통부_건축물대장정보 서비스
- **용도**: 건물 상세 정보 (준공일, 구조, 용도 등)
- **활용도**: ⭐⭐⭐⭐

#### 🗺️ 토지 정보
- **API 명**: 국토교통부_토지이용계획정보 서비스
- **용도**: 용도지역, 지목 등 토지 정보
- **활용도**: ⭐⭐⭐

## 📋 2. API 통합 구현 계획

### 2.1 단계별 구현 로드맵

#### Phase 1: 핵심 실거래가 API 통합 (1주차)
```javascript
// 구현 예정 API 목록
const PHASE1_APIS = {
  apartmentSales: '아파트 매매 실거래가',
  apartmentRent: '아파트 전월세 실거래가',
  officetelSales: '오피스텔 매매 실거래가',
  officetelRent: '오피스텔 전월세 실거래가'
};
```

#### Phase 2: 부가 정보 API 통합 (2주차)
```javascript
const PHASE2_APIS = {
  buildingInfo: '건축물대장 정보',
  priceIndex: '실거래가격지수',
  landInfo: '토지이용계획정보'
};
```

#### Phase 3: 데이터 분석 및 예측 (3주차)
- 실거래가 트렌드 분석
- 시세 예측 모델
- 투자 수익률 계산

### 2.2 기술 구현 방안

#### API 클라이언트 구조
```python
# src/mcp/collectors/public_data_collector.py

class PublicDataCollector:
    """공공데이터포털 API 수집기"""
    
    def __init__(self, service_key: str):
        self.service_key = service_key
        self.base_urls = {
            'apt_trade': 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev',
            'apt_rent': 'http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent',
            'officetel_trade': 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiTrade',
            'officetel_rent': 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiRent'
        }
    
    async def get_apartment_trades(self, lawd_cd: str, deal_ymd: str):
        """아파트 매매 실거래가 조회"""
        params = {
            'serviceKey': self.service_key,
            'LAWD_CD': lawd_cd,  # 지역코드 (5자리)
            'DEAL_YMD': deal_ymd  # 거래년월 (6자리)
        }
        # API 호출 및 XML 파싱
        
    async def get_apartment_rents(self, lawd_cd: str, deal_ymd: str):
        """아파트 전월세 실거래가 조회"""
        # 구현
```

#### 데이터 모델 설계
```python
# src/models/public_data_models.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ApartmentTrade(BaseModel):
    """아파트 매매 실거래가 모델"""
    deal_amount: int  # 거래금액 (만원)
    deal_year: int
    deal_month: int
    deal_day: int
    apartment_name: str
    exclusive_area: float  # 전용면적
    floor: int
    build_year: int
    road_name: str
    legal_dong: str
    jibun: str
    regional_code: str
    
class ApartmentRent(BaseModel):
    """아파트 전월세 모델"""
    deposit_amount: int  # 보증금 (만원)
    monthly_rent: int  # 월세 (만원)
    contract_year: int
    contract_month: int
    contract_term: str  # 계약기간
    apartment_name: str
    exclusive_area: float
    floor: int
```

### 2.3 데이터 통합 전략

#### 기존 시스템과의 통합
```javascript
// pages/api/public-data.js

export default async function handler(req, res) {
  const { address, type = 'trade' } = req.query;
  
  // 주소를 지역코드로 변환
  const lawdCode = await convertAddressToLawdCode(address);
  
  // 공공데이터 API 호출
  const publicData = await fetchPublicData(lawdCode, type);
  
  // 기존 네이버, 직방, 다방 데이터와 병합
  const mergedData = mergeWithExistingData(publicData);
  
  return res.json({
    success: true,
    publicData,
    mergedData
  });
}
```

## 🔑 3. API 인증 및 설정

### 3.1 서비스키 발급 절차
1. 공공데이터포털 회원가입 (https://www.data.go.kr)
2. 원하는 API 활용신청
3. 서비스키 발급 (즉시 ~ 24시간)
4. 개발/운영 단계별 요청 한도 설정

### 3.2 환경변수 설정
```env
# .env
PUBLIC_DATA_SERVICE_KEY=your_service_key_here
PUBLIC_DATA_ENCODING_KEY=your_encoding_key_here
PUBLIC_DATA_DECODING_KEY=your_decoding_key_here
```

## 📊 4. 데이터 활용 방안

### 4.1 실시간 시세 비교
- 현재 호가 vs 실거래가 비교
- 적정 가격 산정
- 거래 활성도 분석

### 4.2 투자 분석 기능
```python
class InvestmentAnalyzer:
    """투자 분석 도구"""
    
    def calculate_rental_yield(self, purchase_price, monthly_rent):
        """임대 수익률 계산"""
        annual_rent = monthly_rent * 12
        return (annual_rent / purchase_price) * 100
    
    def analyze_price_trend(self, historical_trades):
        """가격 추이 분석"""
        # 6개월, 1년, 3년 추이
        
    def compare_with_average(self, current_price, area_average):
        """지역 평균 대비 분석"""
        # 평균 대비 높음/낮음 판단
```

### 4.3 리포트 생성
- 월별 거래 동향 리포트
- 지역별 시세 변동 리포트
- 투자 수익률 분석 리포트

## 🚀 5. 구현 우선순위

### 즉시 구현 (Must Have)
1. ✅ 아파트 매매 실거래가 API
2. ✅ 아파트 전월세 실거래가 API
3. ✅ 지역코드 변환 기능
4. ✅ 실거래가 표시 UI

### 단기 구현 (Should Have)
1. 오피스텔 실거래가 API
2. 건축물대장 정보 연동
3. 가격 추이 차트
4. 실거래가 vs 호가 비교

### 장기 구현 (Nice to Have)
1. AI 기반 가격 예측
2. 투자 수익률 계산기
3. 맞춤형 매물 추천
4. 실거래가 알림 서비스

## 📈 6. 예상 효과

### 사용자 가치
- **정확한 시세 정보**: 실제 거래된 가격 확인
- **투명한 거래**: 적정 가격 판단 근거
- **투자 의사결정**: 데이터 기반 분석

### 비즈니스 가치
- **차별화**: 공공데이터 기반 신뢰도
- **수익 모델**: 프리미엄 분석 서비스
- **확장성**: 다양한 부가 서비스 가능

## 🔧 7. 기술적 고려사항

### API 제한사항
- 일일 요청 한도: 개발(1만건), 운영(무제한 신청 가능)
- 응답 형식: XML (JSON 변환 필요)
- 지역코드: 법정동 코드 5자리 필요

### 성능 최적화
```python
# 캐싱 전략
class PublicDataCache:
    def __init__(self):
        self.redis = Redis()
        self.cache_ttl = 3600  # 1시간
    
    async def get_or_fetch(self, key, fetcher):
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        data = await fetcher()
        await self.redis.setex(key, self.cache_ttl, json.dumps(data))
        return data
```

### 에러 처리
- API 응답 실패 시 재시도
- 서비스키 만료 체크
- XML 파싱 에러 처리

## 📅 8. 구현 일정

### Week 1
- [ ] 공공데이터포털 API 키 발급
- [ ] 아파트 매매 실거래가 API 연동
- [ ] 지역코드 변환 모듈 개발
- [ ] 기본 UI 통합

### Week 2
- [ ] 전월세 실거래가 API 연동
- [ ] 오피스텔 데이터 통합
- [ ] 캐싱 시스템 구현
- [ ] 실거래가 비교 UI

### Week 3
- [ ] 건축물대장 정보 연동
- [ ] 가격 추이 분석 기능
- [ ] 리포트 생성 기능
- [ ] 성능 최적화

## 🎯 9. 성공 지표

### 기술 지표
- API 응답 속도 < 2초
- 캐시 적중률 > 80%
- 에러율 < 1%

### 비즈니스 지표
- 실거래가 조회 수 증가
- 사용자 체류 시간 증가
- 매물 문의 전환율 향상

---

**작성일**: 2025-01-17
**작성자**: Claude AI Assistant
**버전**: 1.0