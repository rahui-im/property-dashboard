import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Dashboard from '../components/Dashboard';

export default function Home() {
  const [data, setData] = useState(null);

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

  return (
    <>
      <Head>
        <title>강남구 삼성1동 부동산 대시보드</title>
        <meta name="description" content="삼성1동 부동산 매물 분석 대시보드" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet" />
      </Head>
      
      <main style={{ 
        fontFamily: "'Noto Sans KR', sans-serif",
        background: '#f5f7fa',
        minHeight: '100vh',
        padding: '20px'
      }}>
        {data ? (
          <Dashboard data={data} />
        ) : (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100vh' 
          }}>
            <div>데이터 로딩 중...</div>
          </div>
        )}
      </main>
    </>
  );
}