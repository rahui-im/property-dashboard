# 🏢 국토교통부 부동산 실거래가 API 가이드

## 📌 핵심 API 목록

### 1. 아파트매매 실거래 상세 자료
**서비스명**: getRTMSDataSvcAptTradeDev
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev
```

**요청 파라미터**:
- `serviceKey`: 인증키 (필수)
- `pageNo`: 페이지 번호
- `numOfRows`: 한 페이지 결과 수
- `LAWD_CD`: 지역코드 (필수) - 5자리
- `DEAL_YMD`: 계약년월 (필수) - 6자리 (예: 202401)

**주요 응답 항목**:
```xml
<item>
    <거래금액>150,000</거래금액>  <!-- 만원 단위 -->
    <거래유형>중개거래</거래유형>
    <년>2024</년>
    <월>1</월>
    <일>15</일>
    <법정동>삼성동</법정동>
    <아파트>래미안</아파트>
    <전용면적>84.95</전용면적>
    <층>10</층>
    <건축년도>2010</건축년도>
    <도로명>테헤란로</도로명>
    <도로명건물본번호코드>0521</도로명건물본번호코드>
    <도로명건물부번호코드>0000</도로명건물부번호코드>
    <지번>159</지번>
    <지역코드>11680</지역코드>
    <해제사유발생일></해제사유발생일>
    <해제여부>O</해제여부>
</item>
```

### 2. 아파트 전월세 자료
**서비스명**: getRTMSDataSvcAptRent
**요청 URL**:
```
http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent
```

**요청 파라미터**: 매매와 동일

**주요 응답 항목**:
```xml
<item>
    <보증금액>50,000</보증금액>  <!-- 만원 단위 -->
    <월세금액>100</월세금액>     <!-- 만원 단위 -->
    <계약구분>신규</계약구분>
    <계약기간>24</계약기간>       <!-- 개월 -->
    <년>2024</년>
    <월>1</월>
    <일>20</일>
    <법정동>삼성동</법정동>
    <아파트>아이파크</아파트>
    <전용면적>59.95</전용면적>
    <층>5</층>
    <건축년도>2015</건축년도>
    <지번>150-11</지번>
</item>
```

### 3. 오피스텔 매매 신고 자료
**서비스명**: getRTMSDataSvcOffiTrade
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiTrade
```

### 4. 오피스텔 전월세 자료
**서비스명**: getRTMSDataSvcOffiRent
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiRent
```

### 5. 연립다세대 매매 실거래가
**서비스명**: getRTMSDataSvcRHTrade
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcRHTrade
```

### 6. 연립다세대 전월세 자료
**서비스명**: getRTMSDataSvcRHRent
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcRHRent
```

### 7. 단독/다가구 매매 실거래가
**서비스명**: getRTMSDataSvcSHTrade
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcSHTrade
```

### 8. 단독/다가구 전월세 자료
**서비스명**: getRTMSDataSvcSHRent
**요청 URL**:
```
http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcSHRent
```

## 📍 지역코드 (LAWD_CD) 예시

### 서울특별시 주요 구
- 강남구: 11680
- 서초구: 11650
- 송파구: 11710
- 강동구: 11740
- 종로구: 11110
- 중구: 11140
- 용산구: 11170
- 성동구: 11200
- 광진구: 11215
- 동대문구: 11230
- 중랑구: 11260
- 성북구: 11290
- 강북구: 11305
- 도봉구: 11320
- 노원구: 11350
- 은평구: 11380
- 서대문구: 11410
- 마포구: 11440
- 양천구: 11470
- 강서구: 11500
- 구로구: 11530
- 금천구: 11545
- 영등포구: 11560
- 동작구: 11590
- 관악구: 11620

### 경기도 주요 시
- 수원시: 41110
- 성남시: 41130
- 고양시: 41280
- 용인시: 41460
- 부천시: 41190
- 안산시: 41270
- 안양시: 41170
- 의정부시: 41150
- 평택시: 41220
- 시흥시: 41390
- 파주시: 41480
- 김포시: 41570
- 광명시: 41210
- 광주시: 41610
- 하남시: 41450

## 🔧 구현 예제

### Python 구현
```python
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

class MOLITAPIClient:
    def __init__(self, service_key):
        self.service_key = service_key
        
    def get_apartment_trades(self, lawd_cd, deal_ymd):
        """아파트 매매 실거래가 조회"""
        url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
        
        params = {
            'serviceKey': self.service_key,
            'LAWD_CD': lawd_cd,  # 예: '11680' (강남구)
            'DEAL_YMD': deal_ymd,  # 예: '202401' (2024년 1월)
            'pageNo': 1,
            'numOfRows': 100
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # XML 파싱
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            trades = []
            for item in items:
                trade = {
                    'deal_amount': self._parse_amount(item.find('거래금액').text),
                    'deal_date': f"{item.find('년').text}-{item.find('월').text}-{item.find('일').text}",
                    'apartment_name': item.find('아파트').text,
                    'area': float(item.find('전용면적').text),
                    'floor': item.find('층').text,
                    'dong': item.find('법정동').text,
                    'jibun': item.find('지번').text if item.find('지번') is not None else '',
                    'build_year': item.find('건축년도').text
                }
                trades.append(trade)
            
            return trades
        else:
            raise Exception(f"API Error: {response.status_code}")
    
    def _parse_amount(self, amount_str):
        """금액 문자열을 숫자로 변환 (만원 단위)"""
        return int(amount_str.replace(',', '').strip())

# 사용 예시
client = MOLITAPIClient('YOUR_SERVICE_KEY')
trades = client.get_apartment_trades('11680', '202401')
for trade in trades:
    print(f"{trade['apartment_name']} - {trade['deal_amount']}만원")
```

### JavaScript/Node.js 구현
```javascript
// pages/api/molit-trades.js
import axios from 'axios';
import xml2js from 'xml2js';

export default async function handler(req, res) {
  const { lawdCd, dealYmd } = req.query;
  
  const serviceKey = process.env.MOLIT_SERVICE_KEY;
  const url = 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev';
  
  try {
    const response = await axios.get(url, {
      params: {
        serviceKey,
        LAWD_CD: lawdCd || '11680',  // 강남구
        DEAL_YMD: dealYmd || '202401',  // 2024년 1월
        pageNo: 1,
        numOfRows: 100
      }
    });
    
    // XML to JSON 변환
    const parser = new xml2js.Parser();
    const result = await parser.parseStringPromise(response.data);
    
    const items = result.response?.body?.[0]?.items?.[0]?.item || [];
    
    const trades = items.map(item => ({
      dealAmount: parseInt(item['거래금액'][0].replace(/,/g, '').trim()),
      dealDate: `${item['년'][0]}-${item['월'][0]}-${item['일'][0]}`,
      apartmentName: item['아파트'][0],
      area: parseFloat(item['전용면적'][0]),
      floor: item['층'][0],
      dong: item['법정동'][0],
      jibun: item['지번']?.[0] || '',
      buildYear: item['건축년도'][0]
    }));
    
    res.status(200).json({
      success: true,
      count: trades.length,
      trades
    });
  } catch (error) {
    console.error('MOLIT API Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
```

## 🔑 서비스키 발급 방법

1. **공공데이터포털 접속**
   - https://www.data.go.kr

2. **회원가입 및 로그인**

3. **API 검색**
   - "국토교통부 아파트매매" 검색

4. **활용신청**
   - 원하는 API 선택 후 "활용신청" 버튼 클릭
   - 활용목적 작성

5. **승인 및 키 발급**
   - 자동승인: 즉시 사용 가능
   - 수동승인: 1-2일 소요

6. **키 종류**
   - 일반 인증키 (Encoding)
   - 일반 인증키 (Decoding)
   - 둘 다 사용 가능

## ⚠️ 주의사항

1. **일일 트래픽 제한**
   - 개발계정: 1,000 ~ 10,000건
   - 운영계정: 신청에 따라 조정 가능

2. **응답 형식**
   - XML 형식으로만 제공
   - JSON 변환 필요

3. **데이터 업데이트**
   - 매월 10일경 전월 데이터 업데이트
   - 실시간 데이터 아님

4. **개인정보 보호**
   - 동호수 미제공
   - 층 정보만 제공

5. **지역코드 확인**
   - https://www.code.go.kr/stdcode/regCodeL.do
   - 법정동코드 앞 5자리 사용

## 📊 활용 방안

1. **시세 비교**
   - 현재 호가와 실거래가 비교
   - 적정 가격 판단

2. **투자 분석**
   - 가격 추이 분석
   - 수익률 계산

3. **시장 동향**
   - 거래량 분석
   - 인기 단지 파악

4. **리포트 생성**
   - 월별 거래 동향
   - 지역별 시세 변화

---

**작성일**: 2025-01-17
**버전**: 1.0