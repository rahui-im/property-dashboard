import React, { useState } from 'react';

export default function SearchResults({ results }) {
  const [selectedProperty, setSelectedProperty] = useState(null);
  
  if (!results) return null;
  
  if (results.error) {
    return (
      <div style={{
        background: '#fff3cd',
        color: '#856404',
        padding: '20px',
        borderRadius: '10px',
        marginBottom: '20px'
      }}>
        ⚠️ {results.error}
      </div>
    );
  }

  if (results.totalCount === 0) {
    return (
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '15px',
        textAlign: 'center',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
      }}>
        <h3 style={{ color: '#666' }}>검색 결과가 없습니다</h3>
        <p style={{ color: '#999' }}>다른 검색어로 시도해보세요</p>
      </div>
    );
  }

  const formatPrice = (price) => {
    if (!price) return '가격정보 없음';
    if (price >= 10000) {
      return `${(price / 10000).toFixed(1)}억원`;
    }
    return `${price.toLocaleString()}만원`;
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
  
  const getPlatformName = (platform) => {
    const names = {
      'naver': '네이버',
      'zigbang': '직방',
      'dabang': '다방',
      'kb': 'KB부동산',
      'peterpan': '피터팬',
      'speedbank': '스피드뱅크'
    };
    return names[platform] || platform?.toUpperCase();
  };

  return (
    <div>
      {/* 검색 결과 요약 */}
      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '20px',
        marginBottom: '20px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
      }}>
        <h3 style={{ marginBottom: '15px' }}>
          📊 검색 결과: "{results.query}"
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '15px'
        }}>
          <div style={{
            background: '#f8f9fa',
            padding: '15px',
            borderRadius: '10px'
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#667eea' }}>
              {results.totalCount}개
            </div>
            <div style={{ fontSize: '14px', color: '#666' }}>총 매물</div>
          </div>
          
          {results.stats.priceRange.avg && (
            <div style={{
              background: '#f8f9fa',
              padding: '15px',
              borderRadius: '10px'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                {formatPrice(results.stats.priceRange.avg)}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>평균 가격</div>
            </div>
          )}
          
          {results.stats.priceRange.min && (
            <div style={{
              background: '#f8f9fa',
              padding: '15px',
              borderRadius: '10px'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
                {formatPrice(results.stats.priceRange.min)}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>최저가</div>
            </div>
          )}
          
          {results.stats.priceRange.max && (
            <div style={{
              background: '#f8f9fa',
              padding: '15px',
              borderRadius: '10px'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ffc107' }}>
                {formatPrice(results.stats.priceRange.max)}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>최고가</div>
            </div>
          )}
        </div>
      </div>

      {/* 매물 리스트 */}
      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '20px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
      }}>
        <h3 style={{ marginBottom: '20px' }}>🏢 매물 목록</h3>
        
        <div style={{
          display: 'grid',
          gap: '15px'
        }}>
          {results.properties.slice(0, 20).map((property, idx) => (
            <div
              key={property.id || idx}
              style={{
                border: '1px solid #e0e0e0',
                borderRadius: '10px',
                padding: '20px',
                cursor: 'pointer',
                transition: 'all 0.3s',
                background: selectedProperty === idx ? '#f8f9fa' : 'white'
              }}
              onClick={() => setSelectedProperty(selectedProperty === idx ? null : idx)}
              onMouseOver={(e) => {
                if (selectedProperty !== idx) {
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }
              }}
              onMouseOut={(e) => {
                if (selectedProperty !== idx) {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h4 style={{ 
                    marginBottom: '10px',
                    fontSize: '18px',
                    color: '#333'
                  }}>
                    {property.title || `매물 ${idx + 1}`}
                  </h4>
                  
                  <div style={{ marginBottom: '10px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '4px 10px',
                      background: getPlatformColor(property.platform),
                      color: 'white',
                      borderRadius: '15px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      marginRight: '10px'
                    }}>
                      {getPlatformName(property.platform)}
                    </span>
                    
                    {property.type && (
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 10px',
                        background: '#6c757d',
                        color: 'white',
                        borderRadius: '15px',
                        fontSize: '12px',
                        marginRight: '10px'
                      }}>
                        {property.type}
                      </span>
                    )}
                    
                    {property.trade_type && (
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 10px',
                        background: '#17a2b8',
                        color: 'white',
                        borderRadius: '15px',
                        fontSize: '12px'
                      }}>
                        {property.trade_type}
                      </span>
                    )}
                  </div>
                  
                  <p style={{ 
                    color: '#666', 
                    marginBottom: '8px',
                    fontSize: '14px'
                  }}>
                    📍 {property.address}
                  </p>
                  
                  <div style={{ 
                    display: 'flex', 
                    gap: '20px',
                    fontSize: '14px',
                    color: '#666'
                  }}>
                    {property.area && (
                      <span>📐 {property.area}㎡</span>
                    )}
                    {property.floor && (
                      <span>🏢 {property.floor}층</span>
                    )}
                  </div>
                </div>
                
                <div style={{
                  textAlign: 'right',
                  minWidth: '120px'
                }}>
                  <div style={{
                    fontSize: '24px',
                    fontWeight: 'bold',
                    color: '#667eea',
                    marginBottom: '5px'
                  }}>
                    {formatPrice(property.price)}
                  </div>
                  {property.monthly_rent > 0 && (
                    <div style={{ fontSize: '14px', color: '#666' }}>
                      월세 {property.monthly_rent}만원
                    </div>
                  )}
                </div>
              </div>
              
              {selectedProperty === idx && (
                <div style={{
                  marginTop: '20px',
                  paddingTop: '20px',
                  borderTop: '1px solid #e0e0e0'
                }}>
                  <p style={{ marginBottom: '10px', color: '#666' }}>
                    {property.description || '상세 설명이 없습니다'}
                  </p>
                  
                  {property.url && (
                    <a
                      href={property.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-block',
                        padding: '10px 20px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      원본 매물 보기 →
                    </a>
                  )}
                  
                  {property.lat && property.lng && (
                    <div style={{ marginTop: '10px' }}>
                      <a
                        href={`https://map.naver.com/?lng=${property.lng}&lat=${property.lat}&zoom=18`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'inline-block',
                          padding: '10px 20px',
                          background: '#03C75A',
                          color: 'white',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          fontSize: '14px',
                          fontWeight: '500',
                          marginRight: '10px'
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        네이버 지도에서 보기 🗺️
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
        
        {results.properties.length > 20 && (
          <div style={{
            textAlign: 'center',
            marginTop: '20px',
            padding: '20px',
            background: '#f8f9fa',
            borderRadius: '10px'
          }}>
            <p style={{ color: '#666' }}>
              전체 {results.totalCount}개 중 상위 20개만 표시됩니다
            </p>
          </div>
        )}
      </div>
    </div>
  );
}