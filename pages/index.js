import React, { useState } from 'react';
import Head from 'next/head';
import SearchResults from '../components/SearchResults';

export default function Home() {
  const [address, setAddress] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!address.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    
    try {
      // 1. 먼저 주소를 좌표로 변환
      console.log('주소 좌표 변환 시작:', address);
      const geocodeResponse = await fetch(`/api/geocode?address=${encodeURIComponent(address)}`);
      const geocodeData = await geocodeResponse.json();
      console.log('좌표 변환 결과:', geocodeData);
      
      // 좌표 변환 실패 시 에러 메시지 표시
      if (!geocodeData.success) {
        setSearchResults({ 
          error: geocodeData.error || '해당 주소의 정보 없음',
          message: geocodeData.message || '정확한 주소를 입력해주세요',
          query: address,
          totalCount: 0,
          properties: []
        });
        return;
      }
      
      // 2. 좌표를 포함하여 실시간 검색 API 호출 - 네이버, 직방, 다방 동시 검색
      console.log('매물 검색 시작:', address);
      let searchUrl = `/api/realtime-search?address=${encodeURIComponent(address)}&platforms=naver,zigbang,dabang`;
      
      // 좌표가 있으면 추가
      if (geocodeData.lat && geocodeData.lng) {
        searchUrl += `&lat=${geocodeData.lat}&lng=${geocodeData.lng}`;
      }
      
      const response = await fetch(searchUrl);
      const data = await response.json();
      console.log('매물 검색 결과:', data);
      
      // 좌표 정보를 결과에 추가
      data.coordinates = {
        lat: geocodeData.lat,
        lng: geocodeData.lng,
        address: geocodeData.roadAddress || geocodeData.jibunAddress || geocodeData.address
      };
      
      setSearchResults(data);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults({ error: '검색 중 오류가 발생했습니다.' });
    } finally {
      setIsSearching(false);
    }
  };

  const resetSearch = () => {
    setSearchResults(null);
    setHasSearched(false);
    setAddress('');
  };

  const exampleAddresses = [
    "삼성동 150-11",
    "삼성동 151-7",
    "삼성동 159",
    "테헤란로 521"
  ];

  return (
    <>
      <Head>
        <title>삼성동 부동산 검색</title>
        <meta name="description" content="강남구 삼성동 부동산 매물 검색 서비스" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet" />
      </Head>
      
      <main style={{ 
        fontFamily: "'Noto Sans KR', sans-serif",
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        minHeight: '100vh',
        display: 'flex',
        alignItems: hasSearched ? 'flex-start' : 'center',
        justifyContent: 'center',
        padding: '20px',
        paddingTop: hasSearched ? '40px' : '20px',
        transition: 'all 0.5s ease'
      }}>
        <div style={{ 
          width: '100%',
          maxWidth: hasSearched ? '1200px' : '600px',
          transition: 'all 0.5s ease'
        }}>
          {!hasSearched ? (
            // 초기 화면 - 검색창만 크고 예쁘게
            <div style={{
              background: 'white',
              borderRadius: '30px',
              padding: '60px 40px',
              boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              textAlign: 'center'
            }}>
              <h1 style={{
                fontSize: '2.5rem',
                fontWeight: '700',
                marginBottom: '15px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                🏢 삼성동 부동산 검색
              </h1>
              
              <p style={{
                color: '#666',
                fontSize: '18px',
                marginBottom: '40px'
              }}>
                원하시는 주소를 입력하고 매물을 찾아보세요
              </p>

              <form onSubmit={handleSearch}>
                <div style={{
                  position: 'relative',
                  marginBottom: '30px'
                }}>
                  <input
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="예: 삼성동 151-7번지"
                    style={{
                      width: '100%',
                      padding: '20px 60px 20px 25px',
                      fontSize: '18px',
                      border: '3px solid #e0e0e0',
                      borderRadius: '50px',
                      outline: 'none',
                      transition: 'all 0.3s',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#667eea';
                      e.target.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#e0e0e0';
                      e.target.style.boxShadow = 'none';
                    }}
                    disabled={isSearching}
                  />
                  
                  <button
                    type="submit"
                    disabled={isSearching || !address.trim()}
                    style={{
                      position: 'absolute',
                      right: '5px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: '50px',
                      height: '50px',
                      borderRadius: '50%',
                      border: 'none',
                      background: isSearching || !address.trim()
                        ? '#ccc'
                        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      fontSize: '20px',
                      cursor: isSearching || !address.trim() ? 'not-allowed' : 'pointer',
                      transition: 'all 0.3s',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    onMouseOver={(e) => {
                      if (!isSearching && address.trim()) {
                        e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
                      }
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
                    }}
                  >
                    {isSearching ? '⏳' : '🔍'}
                  </button>
                </div>
              </form>

              <div>
                <p style={{
                  fontSize: '14px',
                  color: '#999',
                  marginBottom: '15px'
                }}>
                  빠른 검색:
                </p>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '10px',
                  justifyContent: 'center'
                }}>
                  {exampleAddresses.map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => setAddress(example)}
                      style={{
                        padding: '10px 20px',
                        fontSize: '14px',
                        background: 'white',
                        border: '2px solid #e0e0e0',
                        borderRadius: '25px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        fontWeight: '500'
                      }}
                      onMouseOver={(e) => {
                        e.target.style.borderColor = '#667eea';
                        e.target.style.background = '#667eea';
                        e.target.style.color = 'white';
                        e.target.style.transform = 'scale(1.05)';
                      }}
                      onMouseOut={(e) => {
                        e.target.style.borderColor = '#e0e0e0';
                        e.target.style.background = 'white';
                        e.target.style.color = 'black';
                        e.target.style.transform = 'scale(1)';
                      }}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            // 검색 후 - 결과 표시
            <>
              <div style={{
                background: 'white',
                borderRadius: '20px',
                padding: '25px',
                marginBottom: '20px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '15px'
                }}>
                  <button
                    onClick={resetSearch}
                    style={{
                      padding: '10px 15px',
                      background: 'white',
                      border: '2px solid #e0e0e0',
                      borderRadius: '10px',
                      cursor: 'pointer',
                      fontSize: '16px',
                      transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                      e.target.style.borderColor = '#667eea';
                      e.target.style.background = '#f5f5f5';
                    }}
                    onMouseOut={(e) => {
                      e.target.style.borderColor = '#e0e0e0';
                      e.target.style.background = 'white';
                    }}
                  >
                    ← 새 검색
                  </button>
                  
                  <form onSubmit={handleSearch} style={{ flex: 1 }}>
                    <div style={{ position: 'relative' }}>
                      <input
                        type="text"
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        placeholder="주소 입력..."
                        style={{
                          width: '100%',
                          padding: '12px 50px 12px 20px',
                          fontSize: '16px',
                          border: '2px solid #e0e0e0',
                          borderRadius: '30px',
                          outline: 'none',
                          transition: 'all 0.3s'
                        }}
                        onFocus={(e) => e.target.style.borderColor = '#667eea'}
                        onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
                        disabled={isSearching}
                      />
                      <button
                        type="submit"
                        disabled={isSearching || !address.trim()}
                        style={{
                          position: 'absolute',
                          right: '5px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: '35px',
                          height: '35px',
                          borderRadius: '50%',
                          border: 'none',
                          background: isSearching || !address.trim()
                            ? '#ccc'
                            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          color: 'white',
                          cursor: isSearching || !address.trim() ? 'not-allowed' : 'pointer',
                          transition: 'all 0.3s',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        {isSearching ? '⏳' : '🔍'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
              
              {isSearching ? (
                <div style={{
                  background: 'white',
                  borderRadius: '20px',
                  padding: '60px',
                  textAlign: 'center',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔍</div>
                  <h3 style={{ color: '#667eea', marginBottom: '10px' }}>검색 중...</h3>
                  <p style={{ color: '#666' }}>실시간 매물 정보를 가져오고 있습니다</p>
                </div>
              ) : (
                <SearchResults results={searchResults} />
              )}
            </>
          )}
        </div>
      </main>
    </>
  );
}