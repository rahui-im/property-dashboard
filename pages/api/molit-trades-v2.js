// 국토교통부 아파트 매매 실거래가 API v2 (새로운 엔드포인트)
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
  
  // 현재 날짜를 기본값으로 (YYYYMM 형식) - 전월 데이터 조회
  const currentDate = new Date();
  currentDate.setMonth(currentDate.getMonth() - 1);
  const defaultDealYmd = dealYmd || `${currentDate.getFullYear()}${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
  
  // 주소에서 지역코드 찾기
  let lawdCd = '11680'; // 기본값: 강남구
  
  for (const [key, code] of Object.entries(REGION_CODES)) {
    if (address && address.includes(key.split(' ').pop())) {
      lawdCd = code;
      console.log(`[MOLIT v2] 지역코드 매칭: ${key} -> ${code}`);
      break;
    }
  }
  
  // 새로운 서비스키 사용
  const serviceKey = 'zPJlRCZmK%2FAHQ9ZXvM3tZPfC0EDZKOvNKBjm7z10fmntfhPcnGajlo1eu%2BYKMbul9vZRTqOzl%2BTx4nxM4995pg%3D%3D';
  
  // 새로운 API URL - apis.data.go.kr 도메인 사용
  let apiUrl;
  let serviceName;
  
  if (type === 'trade') {
    // 새로운 엔드포인트 사용
    apiUrl = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev';
    serviceName = 'getRTMSDataSvcAptTradeDev';
  } else if (type === 'rent') {
    // 전월세는 기존과 유사한 패턴으로 추정
    apiUrl = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent';
    serviceName = 'getRTMSDataSvcAptRent';
  } else {
    return res.status(400).json({ error: 'Invalid type. Use "trade" or "rent"' });
  }
  
  try {
    console.log(`[MOLIT v2] API 호출: ${apiUrl}`);
    console.log(`[MOLIT v2] 파라미터: LAWD_CD=${lawdCd}, DEAL_YMD=${defaultDealYmd}`);
    
    // API 호출 - GET 방식
    const response = await axios.get(apiUrl, {
      params: {
        serviceKey: serviceKey,
        LAWD_CD: lawdCd,
        DEAL_YMD: defaultDealYmd,
        pageNo: 1,
        numOfRows: 100,
        type: 'xml'  // XML 응답 명시
      },
      headers: {
        'Accept': 'application/xml',
        'User-Agent': 'Mozilla/5.0'
      },
      timeout: 15000
    });
    
    console.log(`[MOLIT v2] 응답 상태: ${response.status}`);
    
    // 응답 데이터 로깅 (디버깅용)
    if (response.data) {
      console.log(`[MOLIT v2] 응답 데이터 길이: ${response.data.length}`);
      console.log(`[MOLIT v2] 응답 시작 부분: ${response.data.substring(0, 200)}`);
    }
    
    // XML to JSON 변환
    const parser = new xml2js.Parser({ 
      explicitArray: false,
      ignoreAttrs: true,
      tagNameProcessors: [xml2js.processors.stripPrefix]
    });
    
    const result = await parser.parseStringPromise(response.data);
    console.log('[MOLIT v2] XML 파싱 완료');
    
    // 응답 구조 확인 - 다양한 가능성 체크
    let items = [];
    
    // 가능한 응답 구조들을 체크
    if (result?.response?.body?.items?.item) {
      items = result.response.body.items.item;
    } else if (result?.response?.body?.item) {
      items = result.response.body.item;
    } else if (result?.items?.item) {
      items = result.items.item;
    } else if (result?.item) {
      items = result.item;
    }
    
    // 배열 확인
    const itemArray = Array.isArray(items) ? items : (items ? [items] : []);
    
    console.log(`[MOLIT v2] 조회된 매물 수: ${itemArray.length}`);
    
    let properties = [];
    
    if (type === 'trade') {
      // 매매 데이터 처리
      properties = itemArray.map(item => {
        // 금액 파싱 (쉼표 제거 및 숫자 변환)
        const amount = parseInt(String(item['거래금액'] || item['dealAmount'] || '0').replace(/,/g, '').trim());
        
        return {
          id: `MOLIT_V2_TRADE_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          platform: 'molit_v2',
          type: 'trade',
          dealAmount: amount,
          dealAmountString: amount >= 10000 ? `${(amount / 10000).toFixed(1)}억` : `${amount}만`,
          dealDate: `${item['년'] || item['dealYear']}-${String(item['월'] || item['dealMonth']).padStart(2, '0')}-${String(item['일'] || item['dealDay']).padStart(2, '0')}`,
          year: item['년'] || item['dealYear'],
          month: item['월'] || item['dealMonth'],
          day: item['일'] || item['dealDay'],
          apartmentName: item['아파트'] || item['aptNm'] || item['apartmentName'],
          area: parseFloat(item['전용면적'] || item['excluUseAr'] || item['area'] || 0),
          areaPyeong: Math.round(parseFloat(item['전용면적'] || item['excluUseAr'] || item['area'] || 0) * 0.3025),
          floor: item['층'] || item['floor'],
          dong: item['법정동'] || item['umdNm'] || item['dong'],
          jibun: item['지번'] || item['jibun'] || '',
          roadName: item['도로명'] || item['roadNm'] || '',
          buildYear: item['건축년도'] || item['buildYear'],
          dealType: item['거래유형'] || item['dealingGbn'] || '',
          cancelDate: item['해제사유발생일'] || '',
          cancelStatus: item['해제여부'] || 'O',
          regionalCode: item['지역코드'] || item['sggCd'] || lawdCd
        };
      });
    } else if (type === 'rent') {
      // 전월세 데이터 처리
      properties = itemArray.map(item => {
        const deposit = parseInt(String(item['보증금액'] || item['deposit'] || '0').replace(/,/g, '').trim());
        const monthlyRent = parseInt(String(item['월세금액'] || item['monthlyRent'] || '0').replace(/,/g, '').trim());
        
        return {
          id: `MOLIT_V2_RENT_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          platform: 'molit_v2',
          type: 'rent',
          depositAmount: deposit,
          depositAmountString: deposit >= 10000 ? `${(deposit / 10000).toFixed(1)}억` : `${deposit}만`,
          monthlyRent: monthlyRent,
          monthlyRentString: `${monthlyRent}만`,
          contractDate: `${item['년'] || item['dealYear']}-${String(item['월'] || item['dealMonth']).padStart(2, '0')}-${String(item['일'] || item['dealDay']).padStart(2, '0')}`,
          year: item['년'] || item['dealYear'],
          month: item['월'] || item['dealMonth'],
          day: item['일'] || item['dealDay'],
          apartmentName: item['아파트'] || item['aptNm'] || item['apartmentName'],
          area: parseFloat(item['전용면적'] || item['excluUseAr'] || item['area'] || 0),
          areaPyeong: Math.round(parseFloat(item['전용면적'] || item['excluUseAr'] || item['area'] || 0) * 0.3025),
          floor: item['층'] || item['floor'],
          dong: item['법정동'] || item['umdNm'] || item['dong'],
          jibun: item['지번'] || item['jibun'] || '',
          buildYear: item['건축년도'] || item['buildYear'],
          contractType: item['계약구분'] || '',
          contractPeriod: item['계약기간'] || ''
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
        type,
        apiVersion: 'v2'
      },
      totalCount: properties.length,
      properties: properties.slice(0, 50),
      stats,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('[MOLIT v2] API 오류:', error.message);
    
    if (error.response) {
      console.error('[MOLIT v2] 응답 상태:', error.response.status);
      console.error('[MOLIT v2] 응답 데이터:', error.response.data?.substring?.(0, 500));
    }
    
    res.status(500).json({
      success: false,
      error: '실거래가 조회 중 오류가 발생했습니다',
      details: error.message,
      query: {
        address,
        lawdCd,
        dealYmd: defaultDealYmd,
        apiVersion: 'v2'
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
    const amounts = properties.map(p => p.dealAmount).filter(a => a > 0);
    if (amounts.length === 0) {
      return {
        average: 0,
        min: 0,
        max: 0,
        count: 0
      };
    }
    
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
    const deposits = properties.map(p => p.depositAmount).filter(d => d > 0);
    const rents = properties.filter(p => p.monthlyRent > 0).map(p => p.monthlyRent);
    
    if (deposits.length === 0) {
      return {
        averageDeposit: 0,
        minDeposit: 0,
        maxDeposit: 0,
        averageRent: 0,
        count: 0,
        rentCount: 0
      };
    }
    
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