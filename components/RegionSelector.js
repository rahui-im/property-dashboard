import React, { useState, useEffect } from 'react';
import { KOREA_REGIONS, getProvinces, getDistricts, getDongs } from '../data/korea-regions';

export default function RegionSelector({ onRegionSelect, initialRegion = {} }) {
  const [selectedProvince, setSelectedProvince] = useState(initialRegion.province || '');
  const [selectedDistrict, setSelectedDistrict] = useState(initialRegion.district || '');
  const [selectedDong, setSelectedDong] = useState(initialRegion.dong || '');
  
  const [districts, setDistricts] = useState([]);
  const [dongs, setDongs] = useState([]);

  // 시/도 선택 시 구/군 목록 업데이트
  useEffect(() => {
    if (selectedProvince) {
      const districtList = getDistricts(selectedProvince);
      setDistricts(districtList);
      setSelectedDistrict('');
      setSelectedDong('');
      setDongs([]);
    } else {
      setDistricts([]);
      setDongs([]);
    }
  }, [selectedProvince]);

  // 구/군 선택 시 동/읍/면 목록 업데이트
  useEffect(() => {
    if (selectedProvince && selectedDistrict) {
      const dongList = getDongs(selectedProvince, selectedDistrict);
      setDongs(dongList);
      setSelectedDong('');
    } else {
      setDongs([]);
    }
  }, [selectedProvince, selectedDistrict]);

  // 지역 선택 완료 시 부모 컴포넌트에 알림
  useEffect(() => {
    if (onRegionSelect) {
      const region = {
        province: selectedProvince,
        district: selectedDistrict,
        dong: selectedDong,
        fullAddress: formatFullAddress()
      };
      onRegionSelect(region);
    }
  }, [selectedProvince, selectedDistrict, selectedDong]);

  const formatFullAddress = () => {
    let address = '';
    if (selectedProvince) address += selectedProvince;
    if (selectedDistrict) address += ' ' + selectedDistrict;
    if (selectedDong) address += ' ' + selectedDong;
    return address.trim();
  };

  const handleProvinceChange = (e) => {
    setSelectedProvince(e.target.value);
  };

  const handleDistrictChange = (e) => {
    setSelectedDistrict(e.target.value);
  };

  const handleDongChange = (e) => {
    setSelectedDong(e.target.value);
  };

  const handleReset = () => {
    setSelectedProvince('');
    setSelectedDistrict('');
    setSelectedDong('');
  };

  const provinces = getProvinces();

  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      alignItems: 'center',
      flexWrap: 'wrap',
      marginBottom: '20px'
    }}>
      {/* 시/도 선택 */}
      <div style={{ flex: '1', minWidth: '150px' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: '5px',
          fontSize: '14px',
          color: '#666'
        }}>
          시/도
        </label>
        <select
          value={selectedProvince}
          onChange={handleProvinceChange}
          style={{
            width: '100%',
            padding: '10px',
            fontSize: '16px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            background: 'white',
            cursor: 'pointer',
            outline: 'none'
          }}
        >
          <option value="">시/도 선택</option>
          {provinces.map(province => (
            <option key={province} value={province}>{province}</option>
          ))}
        </select>
      </div>

      {/* 구/군 선택 */}
      <div style={{ flex: '1', minWidth: '150px' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: '5px',
          fontSize: '14px',
          color: '#666'
        }}>
          구/군
        </label>
        <select
          value={selectedDistrict}
          onChange={handleDistrictChange}
          disabled={!selectedProvince}
          style={{
            width: '100%',
            padding: '10px',
            fontSize: '16px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            background: selectedProvince ? 'white' : '#f5f5f5',
            cursor: selectedProvince ? 'pointer' : 'not-allowed',
            outline: 'none',
            opacity: selectedProvince ? 1 : 0.6
          }}
        >
          <option value="">구/군 선택</option>
          {districts.map(district => (
            <option key={district} value={district}>{district}</option>
          ))}
        </select>
      </div>

      {/* 동/읍/면 선택 */}
      <div style={{ flex: '1', minWidth: '150px' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: '5px',
          fontSize: '14px',
          color: '#666'
        }}>
          동/읍/면
        </label>
        <select
          value={selectedDong}
          onChange={handleDongChange}
          disabled={!selectedDistrict}
          style={{
            width: '100%',
            padding: '10px',
            fontSize: '16px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            background: selectedDistrict ? 'white' : '#f5f5f5',
            cursor: selectedDistrict ? 'pointer' : 'not-allowed',
            outline: 'none',
            opacity: selectedDistrict ? 1 : 0.6
          }}
        >
          <option value="">동/읍/면 선택 (선택사항)</option>
          {dongs.map(dong => (
            <option key={dong} value={dong}>{dong}</option>
          ))}
        </select>
      </div>

      {/* 초기화 버튼 */}
      {(selectedProvince || selectedDistrict || selectedDong) && (
        <div style={{ minWidth: '80px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '5px',
            fontSize: '14px',
            color: 'transparent'
          }}>
            &nbsp;
          </label>
          <button
            onClick={handleReset}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              border: '2px solid #ff6b6b',
              borderRadius: '8px',
              background: 'white',
              color: '#ff6b6b',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#ff6b6b';
              e.target.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'white';
              e.target.style.color = '#ff6b6b';
            }}
          >
            초기화
          </button>
        </div>
      )}

      {/* 선택된 주소 표시 */}
      {formatFullAddress() && (
        <div style={{
          width: '100%',
          padding: '10px',
          background: '#f0f8ff',
          borderRadius: '8px',
          fontSize: '14px',
          color: '#333'
        }}>
          <strong>선택된 지역:</strong> {formatFullAddress()}
        </div>
      )}
    </div>
  );
}