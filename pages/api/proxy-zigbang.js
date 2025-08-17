// Vercel Serverless Function - 직방 프록시 API
// 직방 실시간 데이터 수집

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
  
  try {
    console.log('[Proxy] 직방 검색:', address);
    
    // 직방 API - 삼성동 지역 geohash
    const geohashMap = {
      '삼성동': 'wydm6',
      '역삼동': 'wydm5',
      '청담동': 'wydm7',
      '논현동': 'wydm4',
      '대치동': 'wydm3'
    };
    
    const geohash = geohashMap[address] || 'wydm6';
    
    // 직방 매물 리스트 API
    const response = await fetch(`https://apis.zigbang.com/v2/items?domain=zigbang&geohash=${geohash}&zoom=16`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.zigbang.com/',
        'Accept': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.items || [];
      
      console.log('[Proxy] 직방 매물 수:', items.length);
      
      // 데이터 가공
      const properties = items.slice(0, 20).map(item => ({
        id: `ZIGBANG_${item.item_id || Date.now()}`,
        platform: 'zigbang',
        title: item.title || `직방 매물`,
        address: item.address || `서울 강남구 ${address}`,
        price: item.deposit || 0,
        area: item.area || 0,
        area_pyeong: Math.round((item.area || 0) * 0.3025),
        floor: item.floor || '',
        type: item.building_type || '원룸',
        trade_type: item.sales_type === 0 ? '월세' : item.sales_type === 1 ? '전세' : '매매',
        monthly_rent: item.rent || 0,
        lat: item.lat || 37.5172,
        lng: item.lng || 127.0473,
        description: item.description || '',
        images: item.images || [],
        url: `https://www.zigbang.com/home/oneroom/${item.item_id}`,
        collected_at: new Date().toISOString()
      }));
      
      res.status(200).json({
        success: true,
        totalCount: properties.length,
        properties: properties
      });
    } else {
      console.error('[Proxy] 직방 API 오류:', response.status);
      res.status(response.status).json({
        success: false,
        error: 'Failed to fetch from Zigbang',
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