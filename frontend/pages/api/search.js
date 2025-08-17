// 주소 검색 API
import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { address } = req.query;
  
  if (!address) {
    return res.status(400).json({ error: '검색할 주소를 입력해주세요' });
  }

  try {
    // 데이터 파일 읽기
    const dataPath = path.join(process.cwd(), 'public', 'data.js');
    const dataContent = fs.readFileSync(dataPath, 'utf8');
    
    // JavaScript 객체로 변환
    const dataStr = dataContent.replace('const propertyData = ', '').replace(/;$/, '');
    const data = JSON.parse(dataStr);
    
    // 주소로 필터링
    const searchTerms = address.toLowerCase().split(' ');
    const filteredProperties = data.properties.filter(property => {
      const propertyAddress = (property.address || '').toLowerCase();
      const propertyTitle = (property.title || '').toLowerCase();
      
      // 모든 검색어가 주소나 제목에 포함되어야 함
      return searchTerms.every(term => 
        propertyAddress.includes(term) || propertyTitle.includes(term)
      );
    });

    // 결과 분석
    const result = {
      query: address,
      totalCount: filteredProperties.length,
      properties: filteredProperties,
      stats: {
        byPlatform: {},
        byType: {},
        priceRange: {
          min: null,
          max: null,
          avg: null
        }
      }
    };

    // 통계 계산
    if (filteredProperties.length > 0) {
      const prices = filteredProperties
        .map(p => p.price)
        .filter(p => p && p > 0);
      
      if (prices.length > 0) {
        result.stats.priceRange = {
          min: Math.min(...prices),
          max: Math.max(...prices),
          avg: prices.reduce((a, b) => a + b, 0) / prices.length
        };
      }

      // 플랫폼별 집계
      filteredProperties.forEach(p => {
        const platform = p.platform || 'unknown';
        result.stats.byPlatform[platform] = (result.stats.byPlatform[platform] || 0) + 1;
        
        const type = p.type || p.property_type || 'unknown';
        result.stats.byType[type] = (result.stats.byType[type] || 0) + 1;
      });
    }

    res.status(200).json(result);
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: '검색 중 오류가 발생했습니다' });
  }
}