import React, { useState } from 'react';

export default function RealtimeSearch({ onSearch }) {
  const [address, setAddress] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [useRealtime, setUseRealtime] = useState(true);
  const [selectedPlatforms, setSelectedPlatforms] = useState('all');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!address.trim()) return;

    setIsSearching(true);
    try {
      let response;
      
      if (useRealtime) {
        // 실시간 API 호출 - Vercel 또는 로컬
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const endpoint = apiUrl ? `${apiUrl}/api/search/realtime` : '/api/realtime-search';
        const url = `${endpoint}?address=${encodeURIComponent(address)}&platforms=${selectedPlatforms}`;
        response = await fetch(url);
      } else {
        // 정적 데이터 검색 (Next.js API)
        response = await fetch(`/api/search?address=${encodeURIComponent(address)}`);
      }
      
      const data = await response.json();
      onSearch(data);
    } catch (error) {
      console.error('Search error:', error);
      onSearch({ error: '검색 중 오류가 발생했습니다. 서버 연결을 확인해주세요.' });
    } finally {
      setIsSearching(false);
    }
  };

  const exampleAddresses = [
    "삼성동 151-7",
    "삼성동 159",
    "봉은사로",
    "테헤란로",
    "삼성그랜드"
  ];

  const platforms = [
    { value: 'all', label: '전체 플랫폼' },
    { value: 'naver', label: '네이버 부동산' },
    { value: 'zigbang', label: '직방' },
    { value: 'dabang', label: '다방' },
    { value: 'kb', label: 'KB부동산' }
  ];

  return (
    <div style={{
      background: 'white',
      borderRadius: '15px',
      padding: '30px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
      marginBottom: '30px'
    }}>
      <h2 style={{ 
        fontSize: '1.8rem', 
        marginBottom: '20px',
        color: '#333'
      }}>
        🔍 실시간 매물 검색
      </h2>
      
      {/* 실시간/정적 모드 전환 */}
      <div style={{
        marginBottom: '20px',
        padding: '15px',
        background: useRealtime ? '#e8f5e9' : '#fff3e0',
        borderRadius: '10px',
        display: 'flex',
        alignItems: 'center',
        gap: '20px'
      }}>
        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={useRealtime}
            onChange={(e) => setUseRealtime(e.target.checked)}
            style={{ marginRight: '8px', width: '20px', height: '20px' }}
          />
          <span style={{ fontWeight: '600', color: useRealtime ? '#2e7d32' : '#666' }}>
            {useRealtime ? '🟢 실시간 모드' : '📁 캐시 모드'}
          </span>
        </label>
        
        {useRealtime && (
          <select
            value={selectedPlatforms}
            onChange={(e) => setSelectedPlatforms(e.target.value)}
            style={{
              padding: '8px 15px',
              borderRadius: '8px',
              border: '2px solid #e0e0e0',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            {platforms.map(platform => (
              <option key={platform.value} value={platform.value}>
                {platform.label}
              </option>
            ))}
          </select>
        )}
        
        <span style={{ fontSize: '12px', color: '#666', flex: 1 }}>
          {useRealtime 
            ? '최신 데이터를 실시간으로 가져옵니다 (5-10초 소요)'
            : '저장된 데이터를 빠르게 검색합니다'}
        </span>
      </div>
      
      <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="예: 서울 강남구 삼성동 151-7번지"
            style={{
              flex: 1,
              padding: '15px 20px',
              fontSize: '16px',
              border: '2px solid #e0e0e0',
              borderRadius: '10px',
              outline: 'none',
              transition: 'border-color 0.3s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#667eea'}
            onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
            disabled={isSearching}
          />
          <button
            type="submit"
            disabled={isSearching || !address.trim()}
            style={{
              padding: '15px 40px',
              fontSize: '16px',
              fontWeight: '600',
              color: 'white',
              background: isSearching || !address.trim() 
                ? '#ccc' 
                : useRealtime 
                  ? 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)'
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: '10px',
              cursor: isSearching || !address.trim() ? 'not-allowed' : 'pointer',
              transition: 'transform 0.2s',
              minWidth: '140px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
            onMouseOver={(e) => !isSearching && (e.target.style.transform = 'scale(1.05)')}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            {isSearching ? (
              <>
                <span style={{
                  display: 'inline-block',
                  width: '16px',
                  height: '16px',
                  border: '2px solid white',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></span>
                검색 중...
              </>
            ) : (
              <>
                {useRealtime ? '🔄' : '🔍'} 검색
              </>
            )}
          </button>
        </div>
      </form>

      <div>
        <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
          예시 검색어:
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {exampleAddresses.map((example, idx) => (
            <button
              key={idx}
              onClick={() => setAddress(example)}
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                background: '#f5f5f5',
                border: '1px solid #e0e0e0',
                borderRadius: '20px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#667eea';
                e.target.style.color = 'white';
                e.target.style.borderColor = '#667eea';
              }}
              onMouseOut={(e) => {
                e.target.style.background = '#f5f5f5';
                e.target.style.color = 'black';
                e.target.style.borderColor = '#e0e0e0';
              }}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
      
      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}