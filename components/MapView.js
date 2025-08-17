import React, { useEffect, useRef } from 'react';

export default function MapView({ address, lat, lng, properties = [] }) {
  const mapRef = useRef(null);
  const naverMapRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    // 네이버 지도 API 스크립트 로드
    const loadNaverMapScript = () => {
      return new Promise((resolve) => {
        if (window.naver && window.naver.maps) {
          resolve();
          return;
        }

        const script = document.createElement('script');
        script.src = `https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=gs49gWmH9D2UbRfED2r_&submodules=geocoder`;
        script.async = true;
        script.onload = resolve;
        document.head.appendChild(script);
      });
    };

    const initMap = async () => {
      await loadNaverMapScript();

      if (!mapRef.current) return;

      const mapOptions = {
        center: new window.naver.maps.LatLng(lat || 37.5172, lng || 127.0473),
        zoom: 15,
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: window.naver.maps.MapTypeControlStyle.BUTTON,
          position: window.naver.maps.Position.TOP_RIGHT
        },
        zoomControl: true,
        zoomControlOptions: {
          style: window.naver.maps.ZoomControlStyle.SMALL,
          position: window.naver.maps.Position.TOP_RIGHT
        }
      };

      // 지도 생성
      naverMapRef.current = new window.naver.maps.Map(mapRef.current, mapOptions);

      // 중심 마커 추가 (검색한 위치)
      if (lat && lng) {
        const centerMarker = new window.naver.maps.Marker({
          position: new window.naver.maps.LatLng(lat, lng),
          map: naverMapRef.current,
          title: address || '검색 위치',
          icon: {
            content: `
              <div style="
                width: 30px;
                height: 30px;
                background: #ff6b6b;
                border: 2px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
              ">
                📍
              </div>
            `,
            anchor: new window.naver.maps.Point(15, 15)
          }
        });

        // 정보창 추가
        const infowindow = new window.naver.maps.InfoWindow({
          content: `
            <div style="padding: 10px; min-width: 150px;">
              <strong>${address || '검색 위치'}</strong>
            </div>
          `
        });

        window.naver.maps.Event.addListener(centerMarker, 'click', () => {
          if (infowindow.getMap()) {
            infowindow.close();
          } else {
            infowindow.open(naverMapRef.current, centerMarker);
          }
        });
      }

      // 매물 마커 추가
      if (properties && properties.length > 0) {
        clearMarkers();
        
        properties.forEach((property, index) => {
          if (property.lat && property.lng) {
            const marker = new window.naver.maps.Marker({
              position: new window.naver.maps.LatLng(property.lat, property.lng),
              map: naverMapRef.current,
              title: property.title,
              icon: {
                content: `
                  <div style="
                    width: 40px;
                    padding: 5px 8px;
                    background: ${getPlatformColor(property.platform)};
                    border: 2px solid white;
                    border-radius: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                  ">
                    ${formatPrice(property.price)}
                  </div>
                `,
                anchor: new window.naver.maps.Point(20, 20)
              }
            });

            const infowindow = new window.naver.maps.InfoWindow({
              content: `
                <div style="padding: 15px; max-width: 300px;">
                  <h4 style="margin: 0 0 10px 0; color: #333;">${property.title}</h4>
                  <p style="margin: 5px 0; color: #666; font-size: 14px;">
                    <strong>가격:</strong> ${formatPrice(property.price)}
                  </p>
                  <p style="margin: 5px 0; color: #666; font-size: 14px;">
                    <strong>면적:</strong> ${property.area}㎡ (${property.area_pyeong}평)
                  </p>
                  <p style="margin: 5px 0; color: #666; font-size: 14px;">
                    <strong>층:</strong> ${property.floor}
                  </p>
                  <p style="margin: 5px 0; color: #666; font-size: 14px;">
                    <strong>유형:</strong> ${property.type} / ${property.trade_type}
                  </p>
                  <a href="${property.url}" target="_blank" style="
                    display: inline-block;
                    margin-top: 10px;
                    padding: 5px 10px;
                    background: ${getPlatformColor(property.platform)};
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 12px;
                  ">
                    상세보기
                  </a>
                </div>
              `
            });

            window.naver.maps.Event.addListener(marker, 'click', () => {
              if (infowindow.getMap()) {
                infowindow.close();
              } else {
                infowindow.open(naverMapRef.current, marker);
              }
            });

            markersRef.current.push(marker);
          }
        });

        // 모든 마커가 보이도록 지도 영역 조정
        if (markersRef.current.length > 0) {
          const bounds = new window.naver.maps.LatLngBounds();
          
          if (lat && lng) {
            bounds.extend(new window.naver.maps.LatLng(lat, lng));
          }
          
          markersRef.current.forEach(marker => {
            bounds.extend(marker.getPosition());
          });

          naverMapRef.current.fitBounds(bounds);
        }
      }
    };

    initMap();

    // 클린업
    return () => {
      clearMarkers();
    };
  }, [address, lat, lng, properties]);

  const clearMarkers = () => {
    markersRef.current.forEach(marker => {
      marker.setMap(null);
    });
    markersRef.current = [];
  };

  const getPlatformColor = (platform) => {
    const colors = {
      'naver': '#03C75A',
      'zigbang': '#FF6B00',
      'dabang': '#4A90E2',
      'kb': '#FFD700',
      'peterpan': '#9C27B0',
      'speedbank': '#F44336'
    };
    return colors[platform] || '#666';
  };

  const formatPrice = (price) => {
    if (!price) return '가격정보 없음';
    if (price >= 10000) {
      return `${(price / 10000).toFixed(1)}억`;
    }
    return `${price.toLocaleString()}만`;
  };

  return (
    <div style={{
      width: '100%',
      height: '500px',
      borderRadius: '15px',
      overflow: 'hidden',
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      marginBottom: '20px',
      position: 'relative'
    }}>
      <div 
        ref={mapRef} 
        style={{ 
          width: '100%', 
          height: '100%' 
        }}
      />
      
      {/* 지도 로딩 중 표시 */}
      {!naverMapRef.current && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          padding: '20px',
          borderRadius: '10px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', marginBottom: '10px' }}>🗺️</div>
            <div>지도를 불러오는 중...</div>
          </div>
        </div>
      )}

      {/* 매물 개수 표시 */}
      {properties && properties.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          background: 'white',
          padding: '10px 15px',
          borderRadius: '20px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          fontSize: '14px',
          fontWeight: 'bold',
          zIndex: 10
        }}>
          🏠 매물 {properties.length}개
        </div>
      )}
    </div>
  );
}