// 네이버 지도 Geocoding API를 사용한 주소-좌표 변환
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

  const { address } = req.query;
  
  if (!address) {
    return res.status(400).json({ error: '주소를 입력해주세요' });
  }

  try {
    // 환경 변수에서 네이버 API 키 가져오기
    const NAVER_CLIENT_ID = process.env.NAVER_CLIENT_ID || 'gs49gWmH9D2UbRfED2r_';
    const NAVER_CLIENT_SECRET = process.env.NAVER_CLIENT_SECRET || '2onfjVGamO';
    
    // 네이버 지도 Geocoding API 호출
    const geocodeUrl = `https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=${encodeURIComponent(address)}`;
    
    console.log('[Geocoding] 요청:', address);
    
    const response = await fetch(geocodeUrl, {
      headers: {
        'X-NCP-APIGW-API-KEY-ID': NAVER_CLIENT_ID,
        'X-NCP-APIGW-API-KEY': NAVER_CLIENT_SECRET
      }
    });
    
    if (!response.ok) {
      console.error('[Geocoding] API 오류:', response.status);
      
      // 네이버 API 실패 시 백업 좌표 사용
      const backupCoordinates = {
        '삼성동': { lat: 37.5172, lng: 127.0473 },
        '역삼동': { lat: 37.5006, lng: 127.0365 },
        '청담동': { lat: 37.5197, lng: 127.0474 },
        '논현동': { lat: 37.5112, lng: 127.0414 },
        '대치동': { lat: 37.4941, lng: 127.0625 },
        '강남구': { lat: 37.5172, lng: 127.0473 },
        '서초구': { lat: 37.4837, lng: 127.0324 },
        '송파구': { lat: 37.5145, lng: 127.1055 }
      };
      
      // 백업 좌표에서 매칭 시도
      for (const [key, coords] of Object.entries(backupCoordinates)) {
        if (address.includes(key)) {
          return res.status(200).json({
            success: true,
            address: address,
            lat: coords.lat,
            lng: coords.lng,
            radius: 1000,
            source: 'backup'
          });
        }
      }
      
      // API 실패 시에도 기본 좌표 반환
      return res.status(200).json({
        success: true,
        address: address,
        lat: 37.5172,
        lng: 127.0473,
        radius: 1500,
        source: 'default',
        note: 'API 호출 실패로 기본 좌표 사용'
      });
    }
    
    const data = await response.json();
    
    if (!data.addresses || data.addresses.length === 0) {
      console.log('[Geocoding] 결과 없음, 기본 좌표 반환');
      
      // 주소에서 키워드 추출하여 기본 좌표 반환
      const backupCoordinates = {
        '삼성동': { lat: 37.5172, lng: 127.0473 },
        '역삼동': { lat: 37.5006, lng: 127.0365 },
        '청담동': { lat: 37.5197, lng: 127.0474 },
        '논현동': { lat: 37.5112, lng: 127.0414 },
        '대치동': { lat: 37.4941, lng: 127.0625 },
        '강남구': { lat: 37.5172, lng: 127.0473 },
        '서초구': { lat: 37.4837, lng: 127.0324 },
        '송파구': { lat: 37.5145, lng: 127.1055 }
      };
      
      // 백업 좌표에서 매칭 시도
      for (const [key, coords] of Object.entries(backupCoordinates)) {
        if (address.includes(key)) {
          return res.status(200).json({
            success: true,
            address: address,
            lat: coords.lat,
            lng: coords.lng,
            radius: 1000,
            source: 'backup',
            note: 'Geocoding API 결과 없음, 백업 좌표 사용'
          });
        }
      }
      
      // 기본값 반환 (강남구 중심)
      return res.status(200).json({
        success: true,
        address: address,
        lat: 37.5172,
        lng: 127.0473,
        radius: 1500,
        source: 'default',
        note: '주소를 찾을 수 없어 강남구 중심 좌표 사용'
      });
    }
    
    // 첫 번째 결과 사용
    const location = data.addresses[0];
    const result = {
      success: true,
      address: address,
      lat: parseFloat(location.y),
      lng: parseFloat(location.x),
      radius: 500,
      source: 'naver',
      roadAddress: location.roadAddress,
      jibunAddress: location.jibunAddress
    };
    
    console.log('[Geocoding] 성공:', result.roadAddress || result.jibunAddress);
    
    return res.status(200).json(result);
  } catch (error) {
    console.error('[Geocoding] 오류:', error.message);
    
    // 오류 발생 시에도 기본 좌표 반환
    console.error('[Geocoding] 오류 발생, 기본 좌표 반환');
    return res.status(200).json({
      success: true,
      address: address,
      lat: 37.5172,
      lng: 127.0473,
      radius: 1500,
      source: 'default',
      note: '오류 발생으로 기본 좌표 사용',
      error: error.message
    });
  }
}