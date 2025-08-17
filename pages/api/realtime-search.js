// Vercel Serverless Function - 실시간 검색 API
export default async function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { address, platforms = 'all' } = req.query;
  
  if (!address) {
    return res.status(400).json({ error: '검색할 주소를 입력해주세요' });
  }

  try {
    const selectedPlatforms = platforms === 'all' 
      ? ['naver', 'zigbang', 'dabang', 'kb', 'peterpan', 'speedbank'] 
      : platforms.split(',');
    
    const allProperties = [];
    const errors = [];

    // 네이버 부동산 검색
    if (selectedPlatforms.includes('naver')) {
      try {
        const naverProps = await searchNaver(address);
        allProperties.push(...naverProps);
      } catch (e) {
        errors.push(`Naver: ${e.message}`);
      }
    }

    // 직방 검색
    if (selectedPlatforms.includes('zigbang')) {
      try {
        const zigbangProps = await searchZigbang(address);
        allProperties.push(...zigbangProps);
      } catch (e) {
        errors.push(`Zigbang: ${e.message}`);
      }
    }

    // 다방 검색
    if (selectedPlatforms.includes('dabang')) {
      try {
        const dabangProps = await searchDabang(address);
        allProperties.push(...dabangProps);
      } catch (e) {
        errors.push(`Dabang: ${e.message}`);
      }
    }

    // KB부동산 검색
    if (selectedPlatforms.includes('kb')) {
      try {
        const kbProps = await searchKB(address);
        allProperties.push(...kbProps);
      } catch (e) {
        errors.push(`KB: ${e.message}`);
      }
    }

    // 피터팬 검색
    if (selectedPlatforms.includes('peterpan')) {
      try {
        const peterpanProps = await searchPeterpan(address);
        allProperties.push(...peterpanProps);
      } catch (e) {
        errors.push(`Peterpan: ${e.message}`);
      }
    }

    // 스피드뱅크 검색
    if (selectedPlatforms.includes('speedbank')) {
      try {
        const speedbankProps = await searchSpeedbank(address);
        allProperties.push(...speedbankProps);
      } catch (e) {
        errors.push(`Speedbank: ${e.message}`);
      }
    }

    // 통계 계산
    const stats = calculateStats(allProperties);

    const result = {
      query: address,
      platforms: selectedPlatforms,
      totalCount: allProperties.length,
      properties: allProperties.slice(0, 100), // 최대 100개
      stats,
      cached: false,
      timestamp: new Date().toISOString(),
      errors: errors.length > 0 ? errors : null
    };

    res.status(200).json(result);
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ 
      error: '검색 중 오류가 발생했습니다',
      details: error.message 
    });
  }
}

// 네이버 부동산 - 국내 최대 부동산 플랫폼
async function searchNaver(address) {
  const properties = [];
  
  try {
    console.log('[Naver] 검색 시작:', address);
    
    // 먼저 네이버 지도 API로 주소를 좌표로 변환
    const NAVER_CLIENT_ID = process.env.NAVER_CLIENT_ID || 'gs49gWmH9D2UbRfED2r_';
    const NAVER_CLIENT_SECRET = process.env.NAVER_CLIENT_SECRET || '2onfjVGamO';
    
    // 네이버 지도 Geocoding API로 주소를 좌표로 변환
    const geocodeUrl = `https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=${encodeURIComponent(address)}`;
    
    const geocodeResponse = await fetch(geocodeUrl, {
      headers: {
        'X-NCP-APIGW-API-KEY-ID': NAVER_CLIENT_ID,
        'X-NCP-APIGW-API-KEY': NAVER_CLIENT_SECRET
      }
    });
    
    let lat = 37.5172;  // 기본값: 삼성동
    let lng = 127.0473;
    let fullAddress = '서울 강남구 삼성동';
    
    if (geocodeResponse.ok) {
      const geocodeData = await geocodeResponse.json();
      if (geocodeData.addresses && geocodeData.addresses.length > 0) {
        const location = geocodeData.addresses[0];
        lat = parseFloat(location.y);
        lng = parseFloat(location.x);
        fullAddress = location.roadAddress || location.jibunAddress || address;
        console.log('[Naver] 좌표 변환 성공:', fullAddress, lat, lng);
      }
    } else {
      console.log('[Naver] Geocoding 실패, 기본 좌표 사용');
    }
    
    // Vercel 환경에서는 프록시 API 사용
    if (process.env.NODE_ENV === 'production' || process.env.VERCEL) {
      const baseUrl = process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}` 
        : 'https://property-dashboard-lime.vercel.app';
      
      const response = await fetch(`${baseUrl}/api/proxy-naver?address=${encodeURIComponent(address)}&lat=${lat}&lng=${lng}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.properties) {
          console.log('[Naver] 프록시로 매물 수신:', data.properties.length);
          return data.properties;
        }
      }
      
      // 프록시도 실패하면 빈 배열 반환
      console.log('[Naver] Vercel 프록시 실패, 실제 데이터 없음');
      return [];
    }
    
    // 로컬 환경에서는 프록시 API 사용
    const proxyResponse = await fetch(`http://localhost:3000/api/proxy-naver?address=${encodeURIComponent(address)}&lat=${lat}&lng=${lng}`);
    
    if (proxyResponse.ok) {
      const proxyData = await proxyResponse.json();
      if (proxyData.success && proxyData.properties) {
        console.log('[Naver] 로컬 프록시로 매물 수신:', proxyData.properties.length);
        return proxyData.properties;
      }
    }
    
    // 프록시도 실패하면 네이버 부동산 직접 호출 시도
    const btm = lat - 0.01;
    const top = lat + 0.01;
    const lft = lng - 0.01;
    const rgt = lng + 0.01;
    
    const url = 'https://m.land.naver.com/cluster/ajax/articleList';
    const params = new URLSearchParams({
      rletTpCd: 'APT:OPST',
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
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://m.land.naver.com/'
      }
    });
    
    console.log('[Naver] 부동산 API 응답 상태:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('[Naver] 데이터 수신:', data.body?.length || 0, '개');
      const items = data.body || [];
      
      for (const item of items.slice(0, 30)) {
        const property = {
          id: `NAVER_${item.atclNo || Date.now()}_${Math.random()}`,
          platform: 'naver',
          title: item.atclNm || item.bildNm || '네이버 매물',
          building: item.bildNm || '',
          address: fullAddress,
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
        };
        
        properties.push(property);
      }
    }
  } catch (error) {
    console.error('[Naver] 검색 오류:', error.message);
    return [];
  }
  
  return properties;
}

// 직방 - 원룸, 오피스텔 전문 플랫폼
async function searchZigbang(address) {
  const properties = [];
  
  try {
    // Vercel 환경에서는 프록시 API 사용
    if (process.env.NODE_ENV === 'production' || process.env.VERCEL) {
      const baseUrl = process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}` 
        : 'https://property-dashboard-lime.vercel.app';
      
      const response = await fetch(`${baseUrl}/api/proxy-zigbang?address=${encodeURIComponent(address)}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.properties) {
          console.log('[Zigbang] 프록시로 매물 수신:', data.properties.length);
          return data.properties;
        }
      }
    }
    
    // 로컬 환경에서는 프록시 API 사용
    const proxyResponse = await fetch(`http://localhost:3000/api/proxy-zigbang?address=${encodeURIComponent(address)}`);
    
    if (proxyResponse.ok) {
      const proxyData = await proxyResponse.json();
      if (proxyData.success && proxyData.properties) {
        console.log('[Zigbang] 로컬 프록시로 매물 수신:', proxyData.properties.length);
        return proxyData.properties;
      }
    }
    
    // 프록시도 실패하면 직접 호출 시도
    const response = await fetch('https://apis.zigbang.com/v2/items?domain=zigbang&geohash=wydm6&zoom=15', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.items || [];
      
      for (const item of items.slice(0, 20)) {
        const property = {
          id: `ZIGBANG_${item.item_id || Date.now()}`,
          platform: 'zigbang',
          title: item.title || `직방 매물 ${item.item_id}`,
          address: item.address || '서울 강남구 삼성동',
          price: Math.floor((item.보증금 || item.deposit || 0) / 10000),
          area: item.전용면적 || item.area || 0,
          floor: item.floor || '',
          type: item.building_type || '원룸',
          trade_type: item.sales_type || '월세',
          monthly_rent: item.월세 || item.rent || 0,
          lat: item.lat || 37.5172,
          lng: item.lng || 127.0473,
          description: item.description || '',
          url: `https://zigbang.com/home/oneroom/${item.item_id || ''}`,
          collected_at: new Date().toISOString()
        };
        
        if (address.toLowerCase().split(' ').some(term => 
          property.address.toLowerCase().includes(term) ||
          property.title.toLowerCase().includes(term)
        )) {
          properties.push(property);
        }
      }
    }
  } catch (error) {
    console.error('Zigbang search error:', error);
  }
  
  return properties;
}

// 다방 - 원룸, 오피스텔 중개 플랫폼
async function searchDabang(address) {
  const properties = [];
  
  try {
    // Vercel 환경에서는 프록시 API 사용
    if (process.env.NODE_ENV === 'production' || process.env.VERCEL) {
      const baseUrl = process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}` 
        : 'https://property-dashboard-lime.vercel.app';
      
      const response = await fetch(`${baseUrl}/api/proxy-dabang?address=${encodeURIComponent(address)}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.properties) {
          console.log('[Dabang] 프록시로 매물 수신:', data.properties.length);
          return data.properties;
        }
      }
    }
    
    // 로컬 환경에서는 프록시 API 사용
    const proxyResponse = await fetch(`http://localhost:3000/api/proxy-dabang?address=${encodeURIComponent(address)}`);
    
    if (proxyResponse.ok) {
      const proxyData = await proxyResponse.json();
      if (proxyData.success && proxyData.properties) {
        console.log('[Dabang] 로컬 프록시로 매물 수신:', proxyData.properties.length);
        return proxyData.properties;
      }
    }
    
    // 프록시도 실패하면 직접 호출 시도
    const response = await fetch('https://www.dabangapp.com/api/3/room/list/search-complex', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
      },
      body: JSON.stringify({
        filters: {
          address: address,
          room_type: [0, 1, 2, 3, 4],
          selling_type: [0, 1, 2]
        }
      })
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.rooms || [];
      
      for (const item of items.slice(0, 20)) {
        const property = {
          id: `DABANG_${item.id || Date.now()}`,
          platform: 'dabang',
          title: item.title || `다방 매물`,
          address: item.address || '서울 강남구 삼성동',
          price: item.price || 0,
          area: item.room_size || 0,
          floor: `${item.floor}층`,
          type: item.room_type_str || '원룸',
          trade_type: item.selling_type_str || '월세',
          monthly_rent: item.rent || 0,
          lat: item.location?.lat || 37.5172,
          lng: item.location?.lng || 127.0473,
          description: item.description || '',
          url: `https://www.dabangapp.com/room/${item.id}`,
          collected_at: new Date().toISOString()
        };
        properties.push(property);
      }
    }
  } catch (error) {
    console.error('Dabang search error:', error);
  }
  
  return properties;
}

// KB부동산 - KB국민은행 부동산 서비스
async function searchKB(address) {
  const properties = [];
  
  try {
    // KB부동산 Liiv ON API
    const response = await fetch('https://api.kbland.kr/land-property/property/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
      },
      body: JSON.stringify({
        searchKeyword: address,
        pageNo: 1,
        pageSize: 20
      })
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.data?.list || [];
      
      for (const item of items) {
        const property = {
          id: `KB_${item.propertyNo || Date.now()}`,
          platform: 'kb',
          title: item.propertyName || 'KB 매물',
          address: item.address || '서울 강남구 삼성동',
          price: item.tradePrice || 0,
          area: item.supplyArea || 0,
          floor: item.floor || '',
          type: item.propertyType || '아파트',
          trade_type: item.tradeType || '매매',
          lat: item.latitude || 37.5172,
          lng: item.longitude || 127.0473,
          description: item.memo || '',
          url: `https://kbland.kr/property/${item.propertyNo}`,
          collected_at: new Date().toISOString()
        };
        properties.push(property);
      }
    }
  } catch (error) {
    console.error('KB search error:', error);
  }
  
  return properties;
}

// 피터팬의 좋은방 구하기 - 쉐어하우스, 원룸 전문
async function searchPeterpan(address) {
  const properties = [];
  
  try {
    // 피터팬 API
    const response = await fetch('https://api.peterpanz.com/houses/search', {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0'
      },
      params: {
        q: address,
        page: 1,
        limit: 20
      }
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.houses || [];
      
      for (const item of items.slice(0, 20)) {
        const property = {
          id: `PETERPAN_${item.id || Date.now()}`,
          platform: 'peterpan',
          title: item.title || '피터팬 매물',
          address: item.address || '서울 강남구 삼성동',
          price: item.deposit || 0,
          area: item.area || 0,
          floor: item.floor || '',
          type: item.house_type || '쉐어하우스',
          trade_type: '월세',
          monthly_rent: item.rent || 0,
          lat: item.lat || 37.5172,
          lng: item.lng || 127.0473,
          description: item.description || '',
          url: `https://www.peterpanz.com/house/${item.id}`,
          collected_at: new Date().toISOString()
        };
        properties.push(property);
      }
    }
  } catch (error) {
    console.error('Peterpan search error:', error);
  }
  
  return properties;
}

// 스피드뱅크 - 급매물 전문 플랫폼
async function searchSpeedbank(address) {
  const properties = [];
  
  try {
    // 스피드뱅크 API (모의 데이터 - 실제 API 연동 시 교체 필요)
    const mockData = [
      {
        id: 'SB001',
        title: '삼성동 급매 아파트',
        address: '서울 강남구 삼성동',
        price: 150000,
        area: 84,
        floor: '15층',
        type: '아파트',
        trade_type: '매매',
        description: '급매물, 가격협의 가능',
        url: 'https://www.speedbank.co.kr'
      }
    ];
    
    for (const item of mockData) {
      if (address.toLowerCase().split(' ').some(term => 
        item.address.toLowerCase().includes(term)
      )) {
        const property = {
          id: `SPEEDBANK_${item.id}`,
          platform: 'speedbank',
          title: item.title,
          address: item.address,
          price: item.price,
          area: item.area,
          floor: item.floor,
          type: item.type,
          trade_type: item.trade_type,
          lat: 37.5172,
          lng: 127.0473,
          description: item.description,
          url: item.url,
          collected_at: new Date().toISOString()
        };
        properties.push(property);
      }
    }
  } catch (error) {
    console.error('Speedbank search error:', error);
  }
  
  return properties;
}


function calculateStats(properties) {
  const stats = {
    byPlatform: {},
    byType: {},
    priceRange: {
      min: null,
      max: null,
      avg: null
    }
  };

  if (properties.length > 0) {
    // 플랫폼별 집계
    for (const prop of properties) {
      const platform = prop.platform || 'unknown';
      stats.byPlatform[platform] = (stats.byPlatform[platform] || 0) + 1;
      
      const type = prop.type || 'unknown';
      stats.byType[type] = (stats.byType[type] || 0) + 1;
    }
    
    // 가격 통계
    const prices = properties
      .map(p => p.price)
      .filter(p => p && p > 0);
    
    if (prices.length > 0) {
      stats.priceRange = {
        min: Math.min(...prices),
        max: Math.max(...prices),
        avg: Math.round(prices.reduce((a, b) => a + b, 0) / prices.length)
      };
    }
  }

  return stats;
}