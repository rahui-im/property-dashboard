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

  const { address = '삼성동', lat = 37.5172, lng = 127.0473 } = req.query;
  
  try {
    console.log('[Proxy] 네이버 부동산 검색:', address);
    
    // 검색 범위 설정
    const btm = parseFloat(lat) - 0.01;
    const top = parseFloat(lat) + 0.01;
    const lft = parseFloat(lng) - 0.01;
    const rgt = parseFloat(lng) + 0.01;
    
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
      
      // 데이터 가공
      const properties = items.slice(0, 30).map(item => ({
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
        collected_at: new Date().toISOString()
      }));
      
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