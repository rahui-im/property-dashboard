import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Dashboard from '../components/Dashboard';
import AddressSearch from '../components/AddressSearch';
import SearchResults from '../components/SearchResults';

export default function Home() {
  const [data, setData] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [viewMode, setViewMode] = useState('search'); // 'search' or 'dashboard'

  useEffect(() => {
    // 정적 데이터 로드
    const script = document.createElement('script');
    script.src = '/data.js';
    script.async = true;
    script.onload = () => {
      if (window.propertyData) {
        setData(window.propertyData);
      }
    };
    document.body.appendChild(script);
  }, []);

  const handleSearch = (results) => {
    setSearchResults(results);
  };

  return (
    <>
      <Head>
        <title>강남구 삼성1동 부동산 검색 시스템</title>
        <meta name="description" content="주소로 검색하는 삼성1동 부동산 매물 시스템" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet" />
      </Head>
      
      <main style={{ 
        fontFamily: "'Noto Sans KR', sans-serif",
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        minHeight: '100vh',
        padding: '20px'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          {/* 헤더 */}
          <header style={{
            background: 'white',
            borderRadius: '15px',
            padding: '30px',
            marginBottom: '30px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
          }}>
            <h1 style={{
              fontSize: '2.5rem',
              fontWeight: '700',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '10px'
            }}>
              🏢 삼성1동 부동산 검색 시스템
            </h1>
            <p style={{ color: '#666', fontSize: '16px' }}>
              주소를 입력하여 관련 매물 정보를 확인하세요
            </p>
          </header>

          {/* 모드 전환 버튼 */}
          <div style={{
            marginBottom: '20px',
            display: 'flex',
            gap: '10px'
          }}>
            <button
              onClick={() => setViewMode('search')}
              style={{
                padding: '12px 24px',
                background: viewMode === 'search' 
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                  : 'white',
                color: viewMode === 'search' ? 'white' : '#666',
                border: viewMode === 'search' ? 'none' : '2px solid #e0e0e0',
                borderRadius: '10px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s'
              }}
            >
              🔍 주소 검색
            </button>
            <button
              onClick={() => setViewMode('dashboard')}
              style={{
                padding: '12px 24px',
                background: viewMode === 'dashboard' 
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                  : 'white',
                color: viewMode === 'dashboard' ? 'white' : '#666',
                border: viewMode === 'dashboard' ? 'none' : '2px solid #e0e0e0',
                borderRadius: '10px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s'
              }}
            >
              📊 전체 대시보드
            </button>
          </div>

          {/* 컨텐츠 영역 */}
          {viewMode === 'search' ? (
            <>
              <AddressSearch onSearch={handleSearch} />
              <SearchResults results={searchResults} />
            </>
          ) : (
            data ? (
              <Dashboard data={data} />
            ) : (
              <div style={{
                background: 'white',
                borderRadius: '15px',
                padding: '40px',
                textAlign: 'center',
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳</div>
                <div style={{ color: '#666' }}>데이터 로딩 중...</div>
              </div>
            )
          )}
        </div>
      </main>
    </>
  );
}