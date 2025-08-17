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

  const { address, platforms = 'all', lat, lng } = req.query;
  
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
        const naverProps = await searchNaver(address, lat, lng);
        console.log('[API] Naver 결과:', naverProps.length, '개');
        allProperties.push(...naverProps);
      } catch (e) {
        console.error('[API] Naver 검색 에러:', e);
        errors.push(`Naver: ${e.message}`);
      }
    }

    // 직방 검색
    if (selectedPlatforms.includes('zigbang')) {
      try {
        const zigbangProps = await searchZigbang(address);
        console.log('[API] Zigbang 결과:', zigbangProps.length, '개');
        allProperties.push(...zigbangProps);
      } catch (e) {
        errors.push(`Zigbang: ${e.message}`);
      }
    }

    // 다방 검색
    if (selectedPlatforms.includes('dabang')) {
      try {
        const dabangProps = await searchDabang(address);
        console.log('[API] Dabang 결과:', dabangProps.length, '개');
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
async function searchNaver(address, queryLat, queryLng) {
  const properties = [];
  
  try {
    console.log('[Naver] 검색 시작:', address, '좌표:', queryLat, queryLng);
    
    // 먼저 네이버 지도 API로 주소를 좌표로 변환
    const NAVER_CLIENT_ID = process.env.NAVER_CLIENT_ID || 'gs49gWmH9D2UbRfED2r_';
    const NAVER_CLIENT_SECRET = process.env.NAVER_CLIENT_SECRET || '2onfjVGamO';
    
    // 쿼리 파라미터로 받은 좌표가 있으면 사용, 없으면 Geocoding API 사용
    let lat = queryLat ? parseFloat(queryLat) : 37.5172;
    let lng = queryLng ? parseFloat(queryLng) : 127.0473;
    let fullAddress = address || '서울 강남구 삼성동';
    
    // 좌표가 없을 때만 Geocoding API 사용
    if (!queryLat || !queryLng) {
      const geocodeUrl = `https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=${encodeURIComponent(address)}`;
      
      try {
        const geocodeResponse = await fetch(geocodeUrl, {
          headers: {
            'X-NCP-APIGW-API-KEY-ID': NAVER_CLIENT_ID,
            'X-NCP-APIGW-API-KEY': NAVER_CLIENT_SECRET
          }
        });
        
        if (geocodeResponse.ok) {
          const geocodeData = await geocodeResponse.json();
          if (geocodeData.addresses && geocodeData.addresses.length > 0) {
            const location = geocodeData.addresses[0];
            lat = parseFloat(location.y);
            lng = parseFloat(location.x);
            fullAddress = location.roadAddress || location.jibunAddress || address;
            console.log('[Naver] 좌표 변환 성공:', fullAddress, lat, lng);
          }
        }
      } catch (err) {
        console.log('[Naver] Geocoding 실패, 기본 좌표 사용:', err.message);
      }
    }
    
    console.log('[Naver] 최종 좌표:', lat, lng);
    
    // Vercel 환경에서는 프록시 API 사용
    if (process.env.NODE_ENV === 'production' || process.env.VERCEL) {
      const baseUrl = process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}` 
        : 'https://property-dashboard-lime.vercel.app';
      
      try {
        const response = await fetch(`${baseUrl}/api/proxy-naver?address=${encodeURIComponent(address)}&lat=${lat}&lng=${lng}`);
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.properties) {
            console.log('[Naver] 프록시로 실제 매물 수신:', data.properties.length);
            return data.properties;
          }
        }
      } catch (fetchError) {
        console.error('[Naver] Vercel 프록시 에러:', fetchError.message);
      }
      
      // 실제 데이터를 가져오지 못한 경우에만 Mock 데이터 사용
      console.log('[Naver] 실제 데이터 없음, Mock 데이터로 대체');
    }
    
    // 로컬 환경에서도 프록시 API 시도 (Vercel이 아닌 경우)
    if (!process.env.NODE_ENV || process.env.NODE_ENV === 'development') {
      try {
        const proxyResponse = await fetch(`http://localhost:3000/api/proxy-naver?address=${encodeURIComponent(address)}&lat=${lat}&lng=${lng}`);
        
        if (proxyResponse.ok) {
          const proxyData = await proxyResponse.json();
          if (proxyData.success && proxyData.properties && proxyData.properties.length > 0) {
            console.log('[Naver] 로컬 프록시로 매물 수신:', proxyData.properties.length);
            return proxyData.properties;
          }
        }
      } catch (localError) {
        console.log('[Naver] 로컬 프록시 연결 실패:', localError.message);
      }
    }
    
    // 실제 데이터가 없으면 빈 배열 반환
    console.log('[Naver] 실제 API 호출 실패, 데이터 없음');
    return [];
  } catch (error) {
    console.error('[Naver] 검색 오류:', error.message);
    // 오류 발생시에도 빈 배열 반환
    return [];
  }
}

// 직방 - 원룸, 오피스텔 전문 플랫폼
async function searchZigbang(address) {
  const properties = [];
  
  try {
    console.log('[Zigbang] 검색 시작:', address);
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
    
    // 프록시도 실패하면 빈 배열 반환
    console.log('[Zigbang] 실제 데이터 없음');
    return [];
  } catch (error) {
    console.error('Zigbang search error:', error);
  }
  
  return properties;
}

// 다방 - 원룸, 오피스텔 중개 플랫폼
async function searchDabang(address) {
  const properties = [];
  
  try {
    console.log('[Dabang] 검색 시작:', address);
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
    
    // 프록시도 실패하면 빈 배열 반환
    console.log('[Dabang] 실제 데이터 없음');
    return [];
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
  // 스피드뱅크는 실제 API 연동 전까지 비활성화
  console.log('[Speedbank] API 미연동 상태');
  return [];
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