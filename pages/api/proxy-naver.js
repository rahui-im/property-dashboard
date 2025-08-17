// Vercel Serverless Function - 네이버 부동산 프록시 API
// CORS 문제 해결을 위한 서버 사이드 프록시

export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const { address = '삼성동' } = req.query;
  
  // 주소로 좌표 찾기
  let lat = 37.5172;
  let lng = 127.0473;
  let searchRadius = 0.005; // 기본 반경 (약 500m)
  
  // 특정 주소별 정확한 좌표
  const addressMap = {
    '삼성동 150-11': { lat: 37.5086, lng: 127.0631, radius: 0.003 },
    '삼성동150-11': { lat: 37.5086, lng: 127.0631, radius: 0.003 },
    '삼성동 151-7': { lat: 37.5089, lng: 127.0635, radius: 0.003 },
    '삼성동 159': { lat: 37.5092, lng: 127.0628, radius: 0.003 },
    '테헤란로 521': { lat: 37.5085, lng: 127.0589, radius: 0.003 },
    '봉은사로 114': { lat: 37.5131, lng: 127.0579, radius: 0.003 },
    '삼성동': { lat: 37.5172, lng: 127.0473, radius: 0.01 },
    '역삼동': { lat: 37.5006, lng: 127.0365, radius: 0.01 },
    '청담동': { lat: 37.5197, lng: 127.0474, radius: 0.01 },
    '대치동': { lat: 37.4941, lng: 127.0625, radius: 0.01 }
  };
  
  // 주소 정규화 (공백 제거)
  const normalizedAddress = address.replace(/\s+/g, ' ').trim();
  
  // 주소 매칭
  for (const [key, coords] of Object.entries(addressMap)) {
    if (normalizedAddress.includes(key) || key.includes(normalizedAddress)) {
      lat = coords.lat;
      lng = coords.lng;
      searchRadius = coords.radius;
      console.log(`[Proxy] 주소 매칭: ${key} -> 좌표: ${lat}, ${lng}`);
      break;
    }
  }
  
  try {
    console.log('[Proxy] 네이버 부동산 검색:', address, '좌표:', lat, lng);
    
    // 검색 범위 설정 (특정 주소는 더 좁은 범위)
    const btm = lat - searchRadius;
    const top = lat + searchRadius;
    const lft = lng - searchRadius;
    const rgt = lng + searchRadius;
    
    // 네이버 부동산 API 직접 호출 (서버 사이드이므로 CORS 문제 없음)
    const url = 'https://m.land.naver.com/cluster/ajax/articleList';
    const params = new URLSearchParams({
      rletTpCd: 'APT:OPST:VL:DDDGG:OR:ABYG:JGC',
      tradTpCd: 'A1:B1:B2',
      z: 16,
      lat: lat,
      lon: lng,
      btm: btm,
      lft: lft,
      top: top,
      rgt: rgt,
      page: 1,
      articleOrder: 'A02',
      showR0: 'true'
    });

    const response = await fetch(`${url}?${params}`, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://m.land.naver.com/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
      }
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.body || [];
      
      console.log('[Proxy] 매물 수:', items.length);
      
      // 데이터 가공 및 거리 필터링
      const properties = [];
      
      for (const item of items) {
        // 거리 계산 (간단한 유클리드 거리)
        const distance = Math.sqrt(
          Math.pow((item.lat || lat) - lat, 2) + 
          Math.pow((item.lng || lng) - lng, 2)
        );
        
        // 특정 주소 검색 시 가까운 매물만 포함
        if (normalizedAddress.includes('삼성동 150') && distance > 0.005) continue;
        if (normalizedAddress.includes('삼성동 151') && distance > 0.005) continue;
        
        properties.push({
        id: `NAVER_${item.atclNo || Date.now()}_${Math.random()}`,
        platform: 'naver',
        title: item.atclNm || item.bildNm || '네이버 매물',
        building: item.bildNm || '',
        address: `서울 강남구 ${address}`,
        price: parseInt(String(item.prc || 0).replace(/[^\d]/g, '')) || 0,
        price_string: item.prc || '0',
        area: parseFloat(item.spc1 || 0),
        area_pyeong: parseFloat(item.spc2 || 0),
        floor: item.flrInfo || '',
        type: item.rletTpNm || '아파트',
        trade_type: item.tradTpNm || '매매',
        lat: item.lat || lat,
        lng: item.lng || lng,
        description: item.atclFetrDesc || '',
        confirm_date: item.cfmYmd || '',
          url: `https://m.land.naver.com/article/info/${item.atclNo || ''}`,
          collected_at: new Date().toISOString(),
          distance: distance
        });
        
        if (properties.length >= 30) break;
      }
      
      // 거리순 정렬
      properties.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      
      res.status(200).json({
        success: true,
        totalCount: properties.length,
        properties: properties
      });
    } else {
      console.error('[Proxy] 네이버 API 오류:', response.status);
      res.status(response.status).json({
        success: false,
        error: 'Failed to fetch from Naver',
        status: response.status
      });
    }
  } catch (error) {
    console.error('[Proxy] 오류:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}