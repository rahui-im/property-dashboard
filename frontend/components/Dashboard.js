import React, { useState } from 'react';
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function Dashboard({ data }) {
  const [selectedTab, setSelectedTab] = useState('overview');
  
  if (!data) return null;

  const { stats, properties, area, collectionTime } = data;

  // 차트 데이터 준비
  const platformData = Object.entries(stats.byPlatform || {}).map(([name, value]) => ({
    name,
    value
  }));

  const typeData = Object.entries(stats.byType || {}).map(([name, value]) => ({
    name,
    value
  }));

  const tradeData = Object.entries(stats.byTrade || {}).map(([name, value]) => ({
    name,
    value
  }));

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '30px',
        borderRadius: '15px',
        marginBottom: '30px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '2.5rem', fontWeight: 700 }}>
          🏢 {area} 부동산 대시보드
        </h1>
        <p style={{ margin: '10px 0 0 0', opacity: 0.9 }}>
          총 {stats.total?.toLocaleString() || 0}개 매물 | 
          수집 시간: {new Date(collectionTime).toLocaleString('ko-KR')}
        </p>
      </div>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <SummaryCard
          title="총 매물 수"
          value={stats.total?.toLocaleString() || '0'}
          icon="🏠"
          color="#667eea"
        />
        <SummaryCard
          title="평균 가격"
          value={`${Math.round((stats.priceRange?.avg || 0) / 10000).toLocaleString()}억`}
          icon="💰"
          color="#00C49F"
        />
        <SummaryCard
          title="최고 가격"
          value={`${Math.round((stats.priceRange?.max || 0) / 10000).toLocaleString()}억`}
          icon="📈"
          color="#FFBB28"
        />
        <SummaryCard
          title="플랫폼 수"
          value={Object.keys(stats.byPlatform || {}).length}
          icon="🌐"
          color="#FF8042"
        />
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '30px',
        borderBottom: '2px solid #e0e0e0',
        paddingBottom: '10px'
      }}>
        <TabButton
          active={selectedTab === 'overview'}
          onClick={() => setSelectedTab('overview')}
        >
          개요
        </TabButton>
        <TabButton
          active={selectedTab === 'properties'}
          onClick={() => setSelectedTab('properties')}
        >
          매물 목록
        </TabButton>
        <TabButton
          active={selectedTab === 'analytics'}
          onClick={() => setSelectedTab('analytics')}
        >
          분석
        </TabButton>
      </div>

      {/* Tab Content */}
      {selectedTab === 'overview' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '30px'
        }}>
          {/* Platform Chart */}
          <ChartCard title="플랫폼별 매물 수">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={platformData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {platformData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Type Chart */}
          <ChartCard title="매물 유형별 분포">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Trade Type Chart */}
          <ChartCard title="거래 유형별 분포">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={tradeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {tradeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Price Range */}
          <ChartCard title="가격 분포">
            <div style={{ padding: '20px' }}>
              <PriceInfo label="최저가" value={stats.priceRange?.min || 0} />
              <PriceInfo label="평균가" value={stats.priceRange?.avg || 0} />
              <PriceInfo label="최고가" value={stats.priceRange?.max || 0} />
            </div>
          </ChartCard>
        </div>
      )}

      {selectedTab === 'properties' && (
        <div style={{
          background: 'white',
          borderRadius: '10px',
          padding: '20px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ marginBottom: '20px' }}>매물 목록 (상위 100개)</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={tableHeaderStyle}>번호</th>
                  <th style={tableHeaderStyle}>플랫폼</th>
                  <th style={tableHeaderStyle}>유형</th>
                  <th style={tableHeaderStyle}>거래</th>
                  <th style={tableHeaderStyle}>매물명</th>
                  <th style={tableHeaderStyle}>가격</th>
                  <th style={tableHeaderStyle}>면적</th>
                  <th style={tableHeaderStyle}>층수</th>
                </tr>
              </thead>
              <tbody>
                {properties.slice(0, 100).map((prop, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={tableCellStyle}>{index + 1}</td>
                    <td style={tableCellStyle}>
                      <span style={getPlatformBadgeStyle(prop.platform)}>
                        {prop.platform || '네이버'}
                      </span>
                    </td>
                    <td style={tableCellStyle}>{prop.type || '-'}</td>
                    <td style={tableCellStyle}>{prop.trade_type || '-'}</td>
                    <td style={tableCellStyle}>{prop.title || '-'}</td>
                    <td style={tableCellStyle}>
                      {prop.price ? `${(prop.price / 10000).toFixed(1)}억` : '-'}
                    </td>
                    <td style={tableCellStyle}>{prop.area ? `${prop.area}㎡` : '-'}</td>
                    <td style={tableCellStyle}>{prop.floor || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedTab === 'analytics' && (
        <div style={{
          background: 'white',
          borderRadius: '10px',
          padding: '30px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ marginBottom: '30px' }}>데이터 분석</h2>
          
          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginBottom: '15px' }}>📊 주요 인사이트</h3>
            <ul style={{ lineHeight: '2' }}>
              <li>가장 많은 매물 유형: <strong>{getTopItem(stats.byType)}</strong></li>
              <li>주요 거래 형태: <strong>{getTopItem(stats.byTrade)}</strong></li>
              <li>가장 많은 데이터 제공 플랫폼: <strong>{getTopItem(stats.byPlatform)}</strong></li>
              <li>가격 범위: <strong>{formatPrice(stats.priceRange?.min)} ~ {formatPrice(stats.priceRange?.max)}</strong></li>
            </ul>
          </div>

          <div>
            <h3 style={{ marginBottom: '15px' }}>💡 투자 추천</h3>
            <div style={{
              background: '#f8f9fa',
              padding: '20px',
              borderRadius: '10px',
              border: '1px solid #e0e0e0'
            }}>
              <p style={{ margin: 0, lineHeight: '1.8' }}>
                현재 {area}의 평균 매매가는 <strong>{formatPrice(stats.priceRange?.avg)}</strong>입니다.
                총 {stats.total?.toLocaleString()}개의 매물 중 아파트가 가장 많은 비중을 차지하고 있으며,
                매매 거래가 전세나 월세보다 활발한 편입니다.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper Components
function SummaryCard({ title, value, icon, color }) {
  return (
    <div style={{
      background: 'white',
      padding: '25px',
      borderRadius: '10px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
      borderLeft: `4px solid ${color}`
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <p style={{ margin: 0, color: '#666', fontSize: '0.9rem' }}>{title}</p>
          <p style={{ margin: '10px 0 0 0', fontSize: '2rem', fontWeight: 'bold', color }}>
            {value}
          </p>
        </div>
        <div style={{ fontSize: '3rem', opacity: 0.3 }}>{icon}</div>
      </div>
    </div>
  );
}

function TabButton({ children, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '10px 20px',
        background: active ? '#667eea' : 'transparent',
        color: active ? 'white' : '#666',
        border: 'none',
        borderRadius: '5px 5px 0 0',
        cursor: 'pointer',
        fontSize: '1rem',
        fontWeight: active ? 'bold' : 'normal',
        transition: 'all 0.3s'
      }}
    >
      {children}
    </button>
  );
}

function ChartCard({ title, children }) {
  return (
    <div style={{
      background: 'white',
      padding: '20px',
      borderRadius: '10px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
    }}>
      <h3 style={{ marginBottom: '20px' }}>{title}</h3>
      {children}
    </div>
  );
}

function PriceInfo({ label, value }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      padding: '10px 0',
      borderBottom: '1px solid #f0f0f0'
    }}>
      <span style={{ color: '#666' }}>{label}</span>
      <span style={{ fontWeight: 'bold', color: '#333' }}>
        {formatPrice(value)}
      </span>
    </div>
  );
}

// Helper Functions
const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

function getTopItem(obj) {
  if (!obj) return '-';
  const entries = Object.entries(obj);
  if (entries.length === 0) return '-';
  const top = entries.reduce((a, b) => a[1] > b[1] ? a : b);
  return `${top[0]} (${top[1].toLocaleString()}개)`;
}

function formatPrice(price) {
  if (!price) return '-';
  if (price > 10000) {
    return `${(price / 10000).toFixed(1)}억원`;
  }
  return `${price.toLocaleString()}만원`;
}

function getPlatformBadgeStyle(platform) {
  const colors = {
    '네이버': '#03C75A',
    '직방': '#FF6B6B',
    '다방': '#4ECDC4',
    'KB부동산': '#FFD93D'
  };
  
  return {
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '0.85rem',
    fontWeight: 'bold',
    color: 'white',
    background: colors[platform] || '#666'
  };
}

const tableHeaderStyle = {
  padding: '12px',
  textAlign: 'left',
  fontWeight: 'bold',
  color: '#333'
};

const tableCellStyle = {
  padding: '12px',
  color: '#666'
};