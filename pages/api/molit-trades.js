// 국토교통부 아파트 매매 실거래가 API
import axios from 'axios';
import xml2js from 'xml2js';

// 지역코드 매핑
const REGION_CODES = {
  // 서울특별시
  '서울 강남구': '11680',
  '서울 서초구': '11650',
  '서울 송파구': '11710',
  '서울 강동구': '11740',
  '서울 종로구': '11110',
  '서울 중구': '11140',
  '서울 용산구': '11170',
  '서울 성동구': '11200',
  '서울 광진구': '11215',
  '서울 동대문구': '11230',
  '서울 중랑구': '11260',
  '서울 성북구': '11290',
  '서울 강북구': '11305',
  '서울 도봉구': '11320',
  '서울 노원구': '11350',
  '서울 은평구': '11380',
  '서울 서대문구': '11410',
  '서울 마포구': '11440',
  '서울 양천구': '11470',
  '서울 강서구': '11500',
  '서울 구로구': '11530',
  '서울 금천구': '11545',
  '서울 영등포구': '11560',
  '서울 동작구': '11590',
  '서울 관악구': '11620',
  
  // 경기도
  '경기 수원시': '41110',
  '경기 성남시': '41130',
  '경기 성남시 분당구': '41135',
  '경기 고양시': '41280',
  '경기 용인시': '41460',
  '경기 부천시': '41190',
  '경기 안산시': '41270',
  '경기 안양시': '41170',
  
  // 강남구 세부 (앞 5자리만 사용)
  '강남구': '11680',
  '삼성동': '11680',
  '역삼동': '11680',
  '논현동': '11680',
  '청담동': '11680',
  '대치동': '11680',
  '개포동': '11680',
  '도곡동': '11680',
  '일원동': '11680',
  '수서동': '11680',
  '세곡동': '11680'
};

export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const { address, dealYmd, type = 'trade' } = req.query;
  
  // 현재 날짜를 기본값으로 (YYYYMM 형식)
  const currentDate = new Date();
  const defaultDealYmd = dealYmd || `${currentDate.getFullYear()}${String(currentDate.getMonth()).padStart(2, '0')}`;
  
  // 주소에서 지역코드 찾기
  let lawdCd = '11680'; // 기본값: 강남구
  
  for (const [key, code] of Object.entries(REGION_CODES)) {
    if (address && address.includes(key.split(' ').pop())) {
      lawdCd = code;
      console.log(`[MOLIT] 지역코드 매칭: ${key} -> ${code}`);
      break;
    }
  }
  
  // 서비스키 (Encoding 키 사용)
  const serviceKey = process.env.MOLIT_SERVICE_KEY_ENCODING || 'zPJlRCZmK%2FAHQ9ZXvM3tC0EDZKOvNKBjm7z10fmntfhPcnGajlo1eu%2BYKMbul9vZRTqOzl%2BTx4nxM4995pg%3D%3D';
  
  // API URL 설정
  let apiUrl;
  if (type === 'trade') {
    apiUrl = 'http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev';
  } else if (type === 'rent') {
    apiUrl = 'http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent';
  } else {
    return res.status(400).json({ error: 'Invalid type. Use "trade" or "rent"' });
  }
  
  try {
    console.log(`[MOLIT] API 호출: ${apiUrl}`);
    console.log(`[MOLIT] 파라미터: LAWD_CD=${lawdCd}, DEAL_YMD=${defaultDealYmd}`);
    
    // API 호출
    const response = await axios.get(apiUrl, {
      params: {
        serviceKey: serviceKey,
        LAWD_CD: lawdCd,
        DEAL_YMD: defaultDealYmd,
        pageNo: 1,
        numOfRows: 100
      },
      timeout: 10000
    });
    
    console.log(`[MOLIT] 응답 상태: ${response.status}`);
    
    // XML to JSON 변환
    const parser = new xml2js.Parser({ 
      explicitArray: false,
      ignoreAttrs: true
    });
    
    const result = await parser.parseStringPromise(response.data);
    console.log('[MOLIT] XML 파싱 완료');
    
    // 응답 데이터 구조 확인
    const items = result?.response?.body?.items?.item || [];
    const itemArray = Array.isArray(items) ? items : [items];
    
    console.log(`[MOLIT] 조회된 매물 수: ${itemArray.length}`);
    
    let properties = [];
    
    if (type === 'trade') {
      // 매매 데이터 처리
      properties = itemArray.map(item => {
        // 금액 파싱 (쉼표 제거 및 숫자 변환)
        const amount = parseInt(String(item['거래금액'] || '0').replace(/,/g, '').trim());
        
        return {
          id: `MOLIT_TRADE_${item['년']}_${item['월']}_${item['일']}_${Math.random().toString(36).substr(2, 9)}`,
          platform: 'molit',
          type: 'trade',
          dealAmount: amount, // 만원 단위
          dealAmountString: `${(amount / 10000).toFixed(1)}억`,
          dealDate: `${item['년']}-${String(item['월']).padStart(2, '0')}-${String(item['일']).padStart(2, '0')}`,
          year: item['년'],
          month: item['월'],
          day: item['일'],
          apartmentName: item['아파트'],
          area: parseFloat(item['전용면적']),
          areaPyeong: Math.round(parseFloat(item['전용면적']) * 0.3025),
          floor: item['층'],
          dong: item['법정동'],
          jibun: item['지번'] || '',
          roadName: item['도로명'] || '',
          buildYear: item['건축년도'],
          dealType: item['거래유형'] || '',
          cancelDate: item['해제사유발생일'] || '',
          cancelStatus: item['해제여부'] || 'O',
          regionalCode: item['지역코드']
        };
      });
    } else if (type === 'rent') {
      // 전월세 데이터 처리
      properties = itemArray.map(item => {
        const deposit = parseInt(String(item['보증금액'] || '0').replace(/,/g, '').trim());
        const monthlyRent = parseInt(String(item['월세금액'] || '0').replace(/,/g, '').trim());
        
        return {
          id: `MOLIT_RENT_${item['년']}_${item['월']}_${item['일']}_${Math.random().toString(36).substr(2, 9)}`,
          platform: 'molit',
          type: 'rent',
          depositAmount: deposit, // 만원 단위
          depositAmountString: deposit >= 10000 ? `${(deposit / 10000).toFixed(1)}억` : `${deposit}만`,
          monthlyRent: monthlyRent, // 만원 단위
          monthlyRentString: `${monthlyRent}만`,
          contractDate: `${item['년']}-${String(item['월']).padStart(2, '0')}-${String(item['일']).padStart(2, '0')}`,
          year: item['년'],
          month: item['월'],
          day: item['일'],
          apartmentName: item['아파트'],
          area: parseFloat(item['전용면적']),
          areaPyeong: Math.round(parseFloat(item['전용면적']) * 0.3025),
          floor: item['층'],
          dong: item['법정동'],
          jibun: item['지번'] || '',
          buildYear: item['건축년도'],
          contractType: item['계약구분'] || '',
          contractPeriod: item['계약기간'] || '',
          previousDeposit: item['종전계약보증금'] || '',
          previousRent: item['종전계약월세'] || ''
        };
      });
    }
    
    // 최신순 정렬
    properties.sort((a, b) => {
      const dateA = new Date(a.dealDate || a.contractDate);
      const dateB = new Date(b.dealDate || b.contractDate);
      return dateB - dateA;
    });
    
    // 통계 계산
    const stats = calculateStats(properties, type);
    
    res.status(200).json({
      success: true,
      query: {
        address,
        lawdCd,
        dealYmd: defaultDealYmd,
        type
      },
      totalCount: properties.length,
      properties: properties.slice(0, 50), // 최대 50개까지만
      stats,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('[MOLIT] API 오류:', error.message);
    
    // 에러 응답 분석
    if (error.response) {
      console.error('[MOLIT] 응답 상태:', error.response.status);
      console.error('[MOLIT] 응답 데이터:', error.response.data);
    }
    
    res.status(500).json({
      success: false,
      error: '실거래가 조회 중 오류가 발생했습니다',
      details: error.message,
      query: {
        address,
        lawdCd,
        dealYmd: defaultDealYmd
      }
    });
  }
}

function calculateStats(properties, type) {
  if (properties.length === 0) {
    return {
      average: 0,
      min: 0,
      max: 0,
      count: 0
    };
  }
  
  if (type === 'trade') {
    const amounts = properties.map(p => p.dealAmount);
    return {
      average: Math.round(amounts.reduce((a, b) => a + b, 0) / amounts.length),
      min: Math.min(...amounts),
      max: Math.max(...amounts),
      count: properties.length,
      averageString: `${(Math.round(amounts.reduce((a, b) => a + b, 0) / amounts.length) / 10000).toFixed(1)}억`,
      minString: `${(Math.min(...amounts) / 10000).toFixed(1)}억`,
      maxString: `${(Math.max(...amounts) / 10000).toFixed(1)}억`
    };
  } else {
    const deposits = properties.map(p => p.depositAmount);
    const rents = properties.filter(p => p.monthlyRent > 0).map(p => p.monthlyRent);
    
    return {
      averageDeposit: Math.round(deposits.reduce((a, b) => a + b, 0) / deposits.length),
      minDeposit: Math.min(...deposits),
      maxDeposit: Math.max(...deposits),
      averageRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
      count: properties.length,
      rentCount: rents.length
    };
  }
}