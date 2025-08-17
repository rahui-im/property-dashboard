import React, { useState } from 'react';

export default function AddressSearch({ onSearch }) {
  const [address, setAddress] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!address.trim()) return;

    setIsSearching(true);
    try {
      const response = await fetch(`/api/search?address=${encodeURIComponent(address)}`);
      const data = await response.json();
      onSearch(data);
    } catch (error) {
      console.error('Search error:', error);
      onSearch({ error: '검색 중 오류가 발생했습니다' });
    } finally {
      setIsSearching(false);
    }
  };

  // 예시 주소들
  const exampleAddresses = [
    "삼성동 151-7",
    "삼성동 159",
    "봉은사로",
    "테헤란로",
    "삼성그랜드"
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
        🔍 주소로 매물 검색
      </h2>
      
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
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: '10px',
              cursor: isSearching || !address.trim() ? 'not-allowed' : 'pointer',
              transition: 'transform 0.2s',
              minWidth: '120px'
            }}
            onMouseOver={(e) => !isSearching && (e.target.style.transform = 'scale(1.05)')}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            {isSearching ? '검색 중...' : '검색'}
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
    </div>
  );
}