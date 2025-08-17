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
      ? ['naver', 'zigbang'] 
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

async function searchNaver(address) {
  const properties = [];
  
  try {
    const url = 'https://m.land.naver.com/cluster/ajax/articleList';
    const params = new URLSearchParams({
      rletTpCd: 'APT:OPST:VL:DDDGG:OR',
      tradTpCd: 'A1:B1:B2:B3',
      z: 15,
      cortarNo: '1168010800', // 강남구 삼성동
      page: 1
    });

    const response = await fetch(`${url}?${params}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://m.land.naver.com/'
      }
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.body || [];
      
      for (const item of items.slice(0, 20)) {
        const property = {
          id: `NAVER_${item.atclNo || Date.now()}`,
          platform: 'naver',
          title: item.atclNm || '',
          address: `서울 강남구 삼성동 ${item.bildNm || ''}`,
          price: parseInt(String(item.prc || 0).replace(/,/g, '')) || 0,
          area: item.spc1 || 0,
          floor: item.flrInfo || '',
          type: item.rletTpNm || '',
          trade_type: item.tradTpNm || '',
          lat: item.lat || 0,
          lng: item.lng || 0,
          description: item.atclFetrDesc || '',
          url: `https://m.land.naver.com/article/info/${item.atclNo || ''}`,
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
    console.error('Naver search error:', error);
  }
  
  return properties;
}

async function searchZigbang(address) {
  const properties = [];
  
  try {
    // 직방 웹 API 사용 (Vercel에서 접근 가능한 공개 API)
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