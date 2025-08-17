"""
직방 수집기
"""
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
from loguru import logger
import json

from .base_collector import BaseCollector


class ZigbangCollector(BaseCollector):
    """직방 수집기"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://apis.zigbang.com"
        self.web_url = "https://www.zigbang.com"
        
    async def collect(self, area: str, room_type: str = "apartment", 
                     trade_type: str = "sales", max_items: int = 100) -> List[Dict]:
        """
        직방에서 매물 수집
        
        Args:
            area: 지역명 (예: "강남구")
            room_type: 매물 유형 (apartment, officetel, villa)
            trade_type: 거래 유형 (sales: 매매, jeonse: 전세, monthly: 월세)
            max_items: 최대 수집 개수
            
        Returns:
            수집된 매물 리스트
        """
        properties = []
        
        try:
            # 1. 지역 ID 조회
            area_id = await self._get_area_id(area)
            if not area_id:
                logger.warning(f"Could not find area ID for {area}")
                return []
                
            # 2. 매물 목록 조회
            items = await self._get_property_list(area_id, room_type, trade_type, max_items)
            
            # 3. 각 매물의 상세 정보 수집
            for item in items[:max_items]:
                try:
                    # 상세 정보 조회
                    detail = await self._get_property_detail(item['item_id'])
                    if detail:
                        # 데이터 정규화
                        normalized = await self.parse_property(detail)
                        if self.validate_property(normalized):
                            properties.append(normalized)
                            
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.debug(f"Error processing item: {e}")
                    
        except Exception as e:
            logger.error(f"Error collecting from Zigbang: {e}")
            
        logger.info(f"Collected {len(properties)} properties from Zigbang for {area}")
        return properties
        
    async def _get_area_id(self, area: str) -> Optional[str]:
        """지역명으로 지역 ID 조회"""
        # 직방의 실제 지역 ID 맵핑 (강남구 삼성1동)
        area_mapping = {
            "강남구": "11680",
            "삼성1동": "1168064000",
            "강남구 삼성1동": "1168064000"
        }
        
        # 먼저 매핑에서 확인
        if area in area_mapping:
            return area_mapping[area]
            
        # API로 검색 시도
        url = f"{self.base_url}/v2/search"
        params = {
            'q': area,
            'serviceType': 'apt'
        }
        
        response = await self.fetch(url, params=params)
        if response and 'items' in response:
            for item in response['items']:
                if area in item.get('name', ''):
                    return str(item.get('id'))
                    
        # 기본값으로 강남구 삼성1동 반환
        return "1168064000"
        
    async def _get_property_list(self, area_id: str, room_type: str, 
                                 trade_type: str, limit: int) -> List[Dict]:
        """매물 목록 조회"""
        items = []
        
        try:
            # 직방의 실제 API 엔드포인트 사용
            if room_type == "apartment":
                # 아파트 매물 조회
                url = f"{self.base_url}/v3/market-price/apartments"
                params = {
                    'region_id': area_id,
                    'sales_type': self._convert_trade_type(trade_type),
                    'sort': 'date',
                    'limit': min(limit, 100)
                }
            else:
                # 원룸/오피스텔 등
                url = f"{self.base_url}/v3/items"
                params = {
                    'region_id': area_id,
                    'sales_type_name': self._convert_trade_type(trade_type),
                    'room_type_name': room_type,
                    'limit': min(limit, 100)
                }
            
            # 여러 페이지 수집
            collected = 0
            page = 0
            
            while collected < limit and page < 10:  # 최대 10페이지
                params['page'] = page
                
                response = await self.fetch(url, params=params)
                if not response:
                    break
                    
                # 응답 구조에 따라 다르게 처리
                page_items = []
                if 'items' in response:
                    page_items = response['items']
                elif 'apartments' in response:
                    page_items = response['apartments']
                elif isinstance(response, list):
                    page_items = response
                    
                if not page_items:
                    break
                    
                items.extend(page_items)
                collected += len(page_items)
                page += 1
                
                # 페이지간 딜레이
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error fetching property list: {e}")
            
        return items[:limit]
        
    async def _get_property_detail(self, item_id: str) -> Optional[Dict]:
        """매물 상세 정보 조회"""
        url = f"{self.base_url}/v3/items/{item_id}"
        
        response = await self.fetch(url)
        if response and 'item' in response:
            return response['item']
            
        return None
        
    def _convert_trade_type(self, trade_type: str) -> str:
        """거래 유형 변환"""
        mapping = {
            'sales': '매매',
            'jeonse': '전세',
            'monthly': '월세'
        }
        return mapping.get(trade_type, '매매')
        
    async def parse_property(self, data: Dict) -> Dict:
        """
        직방 데이터를 표준 형식으로 변환
        
        Args:
            data: 원본 데이터
            
        Returns:
            정규화된 매물 정보
        """
        # 가격 처리
        sales_type = data.get('sales_type', '')
        if sales_type == '매매':
            price = data.get('sales_price', 0)
        elif sales_type == '전세':
            price = data.get('deposit', 0)
        else:  # 월세
            deposit = data.get('deposit', 0)
            rent = data.get('rent', 0)
            price = deposit  # 보증금을 기본 가격으로
            
        parsed = {
            'id': self.create_property_id('zigbang', str(data.get('item_id', ''))),
            'platform': 'zigbang',
            'title': data.get('title', ''),
            'price': price,
            'area': data.get('area', 0),
            'address': data.get('address', ''),
            'description': data.get('description', ''),
            'floor': f"{data.get('floor', '')}층",
            'building_floor': data.get('building_floor', ''),
            'room_type': data.get('room_type', ''),
            'url': f"{self.web_url}/home/items/{data.get('item_id', '')}",
            'collected_at': datetime.now().isoformat(),
            'images': data.get('images', []),
            'lat': data.get('lat'),
            'lng': data.get('lng'),
            'raw_data': data
        }
        
        # 평수 계산
        if parsed['area']:
            parsed['pyeong'] = round(parsed['area'] / 3.3058, 1)
            
        # 월세인 경우 추가 정보
        if sales_type == '월세' and 'rent' in data:
            parsed['monthly_rent'] = data['rent']
            
        return parsed