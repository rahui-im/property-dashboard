// Vercel Serverless Function - 다방 프록시 API
// 다방 실시간 데이터 수집

export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const { address = '삼성동' } = req.query;
  
  // 주소로 좌표 찾기
  let lat = 37.5172;
  let lng = 127.0473;
  let searchRadius = 0.005;
  
  // 특정 주소별 정확한 좌표
  const addressMap = {
    '삼성동 150-11': { lat: 37.5086, lng: 127.0631, radius: 0.003 },
    '삼성동150-11': { lat: 37.5086, lng: 127.0631, radius: 0.003 },
    '삼성동 151-7': { lat: 37.5089, lng: 127.0635, radius: 0.003 },
    '삼성동': { lat: 37.5172, lng: 127.0473, radius: 0.01 },
    '역삼동': { lat: 37.5006, lng: 127.0365, radius: 0.01 },
    '청담동': { lat: 37.5197, lng: 127.0474, radius: 0.01 },
    '대치동': { lat: 37.4941, lng: 127.0625, radius: 0.01 }
  };
  
  // 주소 정규화
  const normalizedAddress = address.replace(/\s+/g, ' ').trim();
  
  // 주소 매칭
  for (const [key, coords] of Object.entries(addressMap)) {
    if (normalizedAddress.includes(key) || key.includes(normalizedAddress)) {
      lat = coords.lat;
      lng = coords.lng;
      searchRadius = coords.radius;
      console.log(`[Proxy] 다방 주소 매칭: ${key} -> 좌표: ${lat}, ${lng}`);
      break;
    }
  }
  
  try {
    console.log('[Proxy] 다방 검색:', address, '좌표:', lat, lng);
    
    // 다방 지역 검색 API
    const searchResponse = await fetch('https://www.dabangapp.com/api/3/room/list/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      body: JSON.stringify({
        api_version: '3.0.1',
        call_type: 'web',
        filters: {
          deposit_range: [0, 999999],
          room_size: [0, 999],
          room_type: [0, 1, 2, 3, 4, 5],
          selling_type: [0, 1, 2],
          location: [[lng - searchRadius, lat - searchRadius], [lng + searchRadius, lat + searchRadius]]
        },
        page: 1
      })
    });

    if (searchResponse.ok) {
      const data = await searchResponse.json();
      const rooms = data.rooms || [];
      
      console.log('[Proxy] 다방 매물 수:', rooms.length);
      
      // 데이터 가공 및 거리 필터링
      const properties = [];
      
      for (const room of rooms) {
        // 거리 계산
        const roomLat = room.location?.lat || lat;
        const roomLng = room.location?.lng || lng;
        const distance = Math.sqrt(
          Math.pow(roomLat - lat, 2) + 
          Math.pow(roomLng - lng, 2)
        );
        
        // 특정 주소 검색 시 가까운 매물만 포함
        if (normalizedAddress.includes('150-11') && distance > 0.005) continue;
        if (normalizedAddress.includes('151-7') && distance > 0.005) continue;
        
        properties.push({
        id: `DABANG_${room.id || Date.now()}`,
        platform: 'dabang',
        title: room.title || '다방 매물',
        address: room.location?.address || `서울 강남구 ${address}`,
        price: room.price_info?.deposit || 0,
        area: room.room_info?.size || 0,
        area_pyeong: Math.round((room.room_info?.size || 0) * 0.3025),
        floor: room.room_info?.floor_string || '',
        type: room.room_type_text || '원룸',
        trade_type: room.selling_type === 0 ? '월세' : room.selling_type === 1 ? '전세' : '매매',
        monthly_rent: room.price_info?.rent || 0,
        lat: room.location?.lat || 37.5172,
        lng: room.location?.lng || 127.0473,
        description: room.description || '',
          url: `https://www.dabangapp.com/room/${room.id}`,
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
      console.error('[Proxy] 다방 API 오류:', searchResponse.status);
      
      // API 실패 시 빈 배열 반환
      res.status(200).json({
        success: false,
        totalCount: 0,
        properties: [],
        error: 'Failed to fetch from Dabang API'
      });
    }
  } catch (error) {
    console.error('[Proxy] 오류:', error.message);
    
    // 오류 시 빈 배열 반환
    res.status(500).json({
      success: false,
      totalCount: 0,
      properties: [],
      error: error.message
    });
  }
}