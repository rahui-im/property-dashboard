"""
다방 수집기
"""
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
from loguru import logger
import json

from .base_collector import BaseCollector


class DabangCollector(BaseCollector):
    """다방 수집기"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.dabangapp.com/api"
        self.web_url = "https://www.dabangapp.com"
        
    async def collect(self, area: str, room_type: str = "apartment", 
                     trade_type: str = "selling", max_items: int = 100) -> List[Dict]:
        """
        다방에서 매물 수집
        
        Args:
            area: 지역명 (예: "강남구")
            room_type: 매물 유형 (apartment, officetel, room)
            trade_type: 거래 유형 (selling: 매매, jeonse: 전세, monthly: 월세)
            max_items: 최대 수집 개수
            
        Returns:
            수집된 매물 리스트
        """
        properties = []
        
        try:
            # 1. 지역 좌표 조회
            lat, lng = await self._get_area_coordinates(area)
            if not lat or not lng:
                logger.warning(f"Could not find coordinates for {area}")
                return []
                
            # 2. 매물 목록 조회
            items = await self._get_property_list(lat, lng, room_type, trade_type, max_items)
            
            # 3. 각 매물의 상세 정보 수집
            for item in items[:max_items]:
                try:
                    # 데이터 정규화 (다방은 목록에 상세 정보 포함)
                    normalized = await self.parse_property(item)
                    if self.validate_property(normalized):
                        properties.append(normalized)
                        
                except Exception as e:
                    logger.debug(f"Error processing item: {e}")
                    
        except Exception as e:
            logger.error(f"Error collecting from Dabang: {e}")
            
        logger.info(f"Collected {len(properties)} properties from Dabang for {area}")
        return properties
        
    async def _get_area_coordinates(self, area: str) -> tuple:
        """지역명으로 좌표 조회"""
        # 서울 주요 구의 대략적인 중심 좌표
        coordinates = {
            "강남구": (37.5172, 127.0473),
            "서초구": (37.4837, 127.0324),
            "송파구": (37.5145, 127.1054),
            "강동구": (37.5301, 127.1237),
            "강서구": (37.5509, 126.8495),
            "마포구": (37.5663, 126.9019),
            "용산구": (37.5324, 126.9905),
            "성동구": (37.5634, 127.0371),
            "광진구": (37.5385, 127.0823),
            "노원구": (37.6542, 127.0568),
            "중구": (37.5641, 126.9979),
            "종로구": (37.5735, 126.9790),
            "성북구": (37.5894, 127.0167),
            "동대문구": (37.5744, 127.0397),
            "중랑구": (37.6063, 127.0925),
            "도봉구": (37.6688, 127.0471),
            "은평구": (37.6027, 126.9293),
            "서대문구": (37.5794, 126.9368),
            "양천구": (37.5171, 126.8664),
            "구로구": (37.4955, 126.8875),
            "금천구": (37.4569, 126.8955),
            "영등포구": (37.5264, 126.8963),
            "동작구": (37.5124, 126.9395),
            "관악구": (37.4784, 126.9516),
            "강북구": (37.6396, 127.0257)
        }
        
        return coordinates.get(area, (None, None))
        
    async def _get_property_list(self, lat: float, lng: float, room_type: str, 
                                 trade_type: str, limit: int) -> List[Dict]:
        """매물 목록 조회"""
        items = []
        
        # API 엔드포인트
        url = f"{self.base_url}/v5/rooms/list"
        
        # 파라미터 설정
        params = {
            'latitude': lat,
            'longitude': lng,
            'radius': 3000,  # 반경 3km
            'room_type': self._convert_room_type(room_type),
            'selling_type': self._convert_trade_type(trade_type),
            'limit': min(limit, 100),
            'offset': 0
        }
        
        response = await self.fetch(url, params=params)
        if response and 'rooms' in response:
            items = response['rooms']
            
        return items
        
    def _convert_room_type(self, room_type: str) -> str:
        """매물 유형 변환"""
        mapping = {
            'apartment': '아파트',
            'officetel': '오피스텔',
            'room': '원룸'
        }
        return mapping.get(room_type, '아파트')
        
    def _convert_trade_type(self, trade_type: str) -> str:
        """거래 유형 변환"""
        mapping = {
            'selling': '매매',
            'jeonse': '전세',
            'monthly': '월세'
        }
        return mapping.get(trade_type, '매매')
        
    async def parse_property(self, data: Dict) -> Dict:
        """
        다방 데이터를 표준 형식으로 변환
        
        Args:
            data: 원본 데이터
            
        Returns:
            정규화된 매물 정보
        """
        # 가격 처리
        selling_type = data.get('selling_type', '')
        if selling_type in ['매매', '전세']:
            price = data.get('price', 0)
        else:  # 월세
            price = data.get('deposit', 0)
            
        parsed = {
            'id': self.create_property_id('dabang', str(data.get('room_id', ''))),
            'platform': 'dabang',
            'title': data.get('title', ''),
            'price': price,
            'area': data.get('area', 0),
            'address': data.get('address', ''),
            'description': data.get('desc', ''),
            'floor': data.get('floor_string', ''),
            'building_floor': data.get('building_floor', ''),
            'room_type': data.get('room_type_string', ''),
            'url': f"{self.web_url}/room/{data.get('room_id', '')}",
            'collected_at': datetime.now().isoformat(),
            'images': data.get('img_urls', []),
            'lat': data.get('latitude'),
            'lng': data.get('longitude'),
            'raw_data': data
        }
        
        # 평수 계산
        if parsed['area']:
            parsed['pyeong'] = round(parsed['area'] / 3.3058, 1)
            
        # 월세인 경우 추가 정보
        if selling_type == '월세' and 'price2' in data:
            parsed['monthly_rent'] = data['price2']
            
        # 추가 정보
        if 'room_options' in data:
            parsed['options'] = data['room_options']
            
        return parsed