import React, { useState, useEffect } from 'react';

export default function RealTradeData({ address }) {
  const [tradeData, setTradeData] = useState(null);
  const [rentData, setRentData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('trade'); // 'trade' or 'rent'

  useEffect(() => {
    if (address) {
      fetchRealTradeData();
    }
  }, [address]);

  const fetchRealTradeData = async () => {
    setLoading(true);
    try {
      // 여러 API 엔드포인트 시도 (fallback 전략)
      const apiEndpoints = [
        '/api/molit-trades-v2',  // 새로운 API (apis.data.go.kr)
        '/api/molit-trades'       // 기존 API (openapi.molit.go.kr)
      ];
      
      let tradeSuccess = false;
      let rentSuccess = false;
      
      // 각 엔드포인트를 순서대로 시도
      for (const endpoint of apiEndpoints) {
        // 매매 데이터 조회
        if (!tradeSuccess) {
          try {
            const tradeResponse = await fetch(`${endpoint}?address=${encodeURIComponent(address)}&type=trade`);
            if (tradeResponse.ok) {
              const tradeResult = await tradeResponse.json();
              if (tradeResult.totalCount > 0) {
                setTradeData(tradeResult);
                tradeSuccess = true;
                console.log(`매매 데이터 성공: ${endpoint}`);
              }
            }
          } catch (e) {
            console.log(`${endpoint} 매매 실패:`, e.message);
          }
        }
        
        // 전월세 데이터 조회
        if (!rentSuccess) {
          try {
            const rentResponse = await fetch(`${endpoint}?address=${encodeURIComponent(address)}&type=rent`);
            if (rentResponse.ok) {
              const rentResult = await rentResponse.json();
              if (rentResult.totalCount > 0) {
                setRentData(rentResult);
                rentSuccess = true;
                console.log(`전월세 데이터 성공: ${endpoint}`);
              }
            }
          } catch (e) {
            console.log(`${endpoint} 전월세 실패:`, e.message);
          }
        }
        
        // 둘 다 성공하면 더 이상 시도하지 않음
        if (tradeSuccess && rentSuccess) break;
      }
    } catch (error) {
      console.error('실거래가 조회 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '30px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '18px', color: '#667eea' }}>
          ⏳ 실거래가 데이터 조회 중...
        </div>
      </div>
    );
  }

  if (!tradeData && !rentData) {
    return null;
  }

  const currentData = activeTab === 'trade' ? tradeData : rentData;

  return (
    <div style={{
      background: 'white',
      borderRadius: '15px',
      padding: '25px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      marginBottom: '20px'
    }}>
      <h2 style={{
        fontSize: '24px',
        fontWeight: 'bold',
        marginBottom: '20px',
        color: '#333',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        📊 국토교통부 실거래가 정보
        <span style={{
          fontSize: '14px',
          color: '#999',
          fontWeight: 'normal'
        }}>
          (최근 거래 기준)
        </span>
      </h2>

      {/* 탭 선택 */}
      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '20px',
        borderBottom: '2px solid #f0f0f0'
      }}>
        <button
          onClick={() => setActiveTab('trade')}
          style={{
            padding: '10px 20px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'trade' ? '2px solid #667eea' : 'none',
            color: activeTab === 'trade' ? '#667eea' : '#999',
            fontSize: '16px',
            fontWeight: activeTab === 'trade' ? 'bold' : 'normal',
            cursor: 'pointer',
            marginBottom: '-2px'
          }}
        >
          매매 ({tradeData?.totalCount || 0}건)
        </button>
        <button
          onClick={() => setActiveTab('rent')}
          style={{
            padding: '10px 20px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'rent' ? '2px solid #667eea' : 'none',
            color: activeTab === 'rent' ? '#667eea' : '#999',
            fontSize: '16px',
            fontWeight: activeTab === 'rent' ? 'bold' : 'normal',
            cursor: 'pointer',
            marginBottom: '-2px'
          }}
        >
          전월세 ({rentData?.totalCount || 0}건)
        </button>
      </div>

      {/* 통계 요약 */}
      {currentData?.stats && (
        <div style={{
          background: '#f8f9fa',
          borderRadius: '10px',
          padding: '15px',
          marginBottom: '20px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px'
        }}>
          {activeTab === 'trade' ? (
            <>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>평균 거래가</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#333' }}>
                  {currentData.stats.averageString}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>최고가</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff6b6b' }}>
                  {currentData.stats.maxString}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>최저가</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#51cf66' }}>
                  {currentData.stats.minString}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>거래 건수</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#667eea' }}>
                  {currentData.stats.count}건
                </div>
              </div>
            </>
          ) : (
            <>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>평균 보증금</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#333' }}>
                  {currentData.stats.averageDeposit >= 10000 
                    ? `${(currentData.stats.averageDeposit / 10000).toFixed(1)}억`
                    : `${currentData.stats.averageDeposit}만`}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>평균 월세</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff6b6b' }}>
                  {currentData.stats.averageRent}만원
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>전세 건수</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#51cf66' }}>
                  {currentData.stats.count - currentData.stats.rentCount}건
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#999' }}>월세 건수</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#667eea' }}>
                  {currentData.stats.rentCount}건
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* 실거래 목록 */}
      <div style={{
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        {currentData?.properties?.map((item, index) => (
          <div key={item.id} style={{
            padding: '15px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            transition: 'background 0.2s',
            cursor: 'pointer'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#f8f9fa'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
          >
            <div style={{ flex: 1 }}>
              <div style={{
                fontWeight: 'bold',
                fontSize: '16px',
                marginBottom: '5px',
                color: '#333'
              }}>
                {item.apartmentName}
              </div>
              <div style={{
                fontSize: '14px',
                color: '#666',
                display: 'flex',
                gap: '15px'
              }}>
                <span>{item.dong} {item.jibun}</span>
                <span>{item.areaPyeong}평 ({item.area}㎡)</span>
                <span>{item.floor}층</span>
                <span>{item.buildYear}년</span>
              </div>
            </div>
            
            <div style={{ textAlign: 'right' }}>
              {activeTab === 'trade' ? (
                <>
                  <div style={{
                    fontSize: '20px',
                    fontWeight: 'bold',
                    color: '#667eea',
                    marginBottom: '5px'
                  }}>
                    {item.dealAmountString}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#999'
                  }}>
                    {item.dealDate}
                  </div>
                </>
              ) : (
                <>
                  <div style={{
                    fontSize: '18px',
                    fontWeight: 'bold',
                    color: '#667eea',
                    marginBottom: '5px'
                  }}>
                    {item.monthlyRent > 0 
                      ? `${item.depositAmountString} / ${item.monthlyRentString}`
                      : item.depositAmountString}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#999'
                  }}>
                    {item.contractDate}
                    {item.contractPeriod && ` (${item.contractPeriod}개월)`}
                  </div>
                </>
              )}
              {item.cancelStatus === 'X' && (
                <div style={{
                  fontSize: '11px',
                  color: '#ff6b6b',
                  marginTop: '3px'
                }}>
                  ⚠️ 해제/취소
                </div>
              )}
            </div>
          </div>
        ))}
        
        {currentData?.properties?.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#999'
          }}>
            해당 지역의 실거래 데이터가 없습니다.
          </div>
        )}
      </div>

      <div style={{
        marginTop: '15px',
        padding: '10px',
        background: '#f0f8ff',
        borderRadius: '8px',
        fontSize: '12px',
        color: '#666'
      }}>
        ℹ️ 국토교통부 실거래가 공개 시스템 제공 데이터 (갱신 주기: 매월)
      </div>
    </div>
  );
}