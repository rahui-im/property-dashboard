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
  
  // 주소로 좌표 찾기
  let lat = 37.5172;
  let lng = 127.0473;
  let geohash = 'wydm6';
  
  // 특정 주소별 정확한 좌표와 geohash
  const addressMap = {
    '삼성동 150-11': { lat: 37.5086, lng: 127.0631, geohash: 'wydm6' },
    '삼성동150-11': { lat: 37.5086, lng: 127.0631, geohash: 'wydm6' },
    '삼성동 151-7': { lat: 37.5089, lng: 127.0635, geohash: 'wydm6' },
    '삼성동': { lat: 37.5172, lng: 127.0473, geohash: 'wydm6' },
    '역삼동': { lat: 37.5006, lng: 127.0365, geohash: 'wydm5' },
    '청담동': { lat: 37.5197, lng: 127.0474, geohash: 'wydm7' },
    '논현동': { lat: 37.5112, lng: 127.0314, geohash: 'wydm4' },
    '대치동': { lat: 37.4941, lng: 127.0625, geohash: 'wydm3' }
  };
  
  // 주소 정규화
  const normalizedAddress = address.replace(/\s+/g, ' ').trim();
  
  // 주소 매칭
  for (const [key, coords] of Object.entries(addressMap)) {
    if (normalizedAddress.includes(key) || key.includes(normalizedAddress)) {
      lat = coords.lat;
      lng = coords.lng;
      geohash = coords.geohash;
      console.log(`[Proxy] 직방 주소 매칭: ${key} -> geohash: ${geohash}`);
      break;
    }
  }
  
  try {
    console.log('[Proxy] 직방 검색:', address, 'geohash:', geohash);
    
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
      
      // 데이터 가공 및 거리 필터링
      const properties = [];
      
      for (const item of items) {
        // 거리 계산
        const itemLat = item.lat || lat;
        const itemLng = item.lng || lng;
        const distance = Math.sqrt(
          Math.pow(itemLat - lat, 2) + 
          Math.pow(itemLng - lng, 2)
        );
        
        // 특정 주소 검색 시 가까운 매물만 포함
        if (normalizedAddress.includes('150-11') && distance > 0.005) continue;
        if (normalizedAddress.includes('151-7') && distance > 0.005) continue;
        
        properties.push({
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
          collected_at: new Date().toISOString(),
          distance: distance
        });
        
        if (properties.length >= 20) break;
      }
      
      // 거리순 정렬
      properties.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      
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