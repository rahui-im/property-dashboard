#!/usr/bin/env python3
"""
실제 직방 API를 사용한 삼성1동 매물 수집기
웹 스크래핑으로 발견한 실제 API 엔드포인트를 사용합니다.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from loguru import logger
import sys

# 한글 출력 설정
sys.stdout.reconfigure(encoding='utf-8')


class ZigbangRealCollector:
    """실제 직방 API를 사용한 수집기"""
    
    def __init__(self):
        self.base_url = "https://apis.zigbang.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Origin': 'https://www.zigbang.com',
            'Referer': 'https://www.zigbang.com/'
        }
        
    async def collect_samsung1dong(self, max_items=2000):
        """삼성1동 매물 수집"""
        properties = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # 1. 아파트 마커 데이터 수집
            apt_properties = await self._collect_apartment_markers(session, max_items // 2)
            properties.extend(apt_properties)
            
            # 2. 오피스텔/원룸 데이터 수집  
            room_properties = await self._collect_room_items(session, max_items // 2)
            properties.extend(room_properties)
            
            # 3. 지역별 가격 정보 수집
            price_properties = await self._collect_price_data(session, max_items // 4)
            properties.extend(price_properties)
            
        logger.info(f"Total collected: {len(properties)} properties from Zigbang")
        return properties
    
    async def _collect_apartment_markers(self, session, max_items):
        """아파트 마커 데이터 수집"""
        properties = []
        
        # 실제 웹에서 사용되는 API 엔드포인트들
        marker_endpoints = [
            f"{self.base_url}/v2/marker/v6/apartment?mode=item&size=3&select=n&level=up1&dpi=160",
            f"{self.base_url}/v2/marker/v6/apartment?mode=item&size=3&select=n&level=up2&dpi=160",
            f"{self.base_url}/v2/marker/v6/apartment?mode=item&size=3&select=n&level=up3&dpi=160",
            f"{self.base_url}/v2/marker/v6/apartment?mode=item&size=3&select=n&level=up4&dpi=160"
        ]
        
        for endpoint in marker_endpoints:
            try:
                # 삼성1동 좌표 범위 추가
                params = {
                    'lat1': 37.508,
                    'lng1': 127.038,
                    'lat2': 37.528,
                    'lng2': 127.058,
                    'zoom': 15
                }
                
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Apartment markers: {len(data) if isinstance(data, list) else 'dict'}")
                        
                        if isinstance(data, list):
                            for item in data[:max_items//4]:
                                prop = self._parse_apartment_marker(item)
                                if prop:
                                    properties.append(prop)
                        elif isinstance(data, dict) and 'items' in data:
                            for item in data['items'][:max_items//4]:
                                prop = self._parse_apartment_marker(item)
                                if prop:
                                    properties.append(prop)
                                    
                        await asyncio.sleep(1)  # Rate limiting
                        
            except Exception as e:
                logger.error(f"Error collecting apartment markers: {e}")
                
        return properties[:max_items]
    
    async def _collect_room_items(self, session, max_items):
        """원룸/오피스텔 아이템 수집"""
        properties = []
        
        try:
            # V3 items API
            url = f"{self.base_url}/v3/items"
            params = {
                'lat1': 37.508,
                'lng1': 127.038,
                'lat2': 37.528,
                'lng2': 127.058,
                'deposit_gte': 0,
                'rent_gte': 0,
                'sales_type[]': '매매',
                'room_type[]': ['원룸', '오피스텔'],
                'limit': max_items
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Room items: {type(data)} - {len(data.get('items', [])) if isinstance(data, dict) else len(data)}")
                    
                    items = data.get('items', []) if isinstance(data, dict) else data
                    for item in items[:max_items]:
                        prop = self._parse_room_item(item)
                        if prop:
                            properties.append(prop)
                            
        except Exception as e:
            logger.error(f"Error collecting room items: {e}")
            
        return properties
    
    async def _collect_price_data(self, session, max_items):
        """지역별 가격 데이터 수집"""
        properties = []
        
        # 실제 웹에서 사용되는 가격 API
        price_endpoints = [
            f"{self.base_url}/apt/locals/prices/on-danjis?minPynArea=10평이하&maxPynArea=60평대이상&geohash=wydm6",
            f"{self.base_url}/apt/locals/prices/on-danjis?minPynArea=10평이하&maxPynArea=60평대이상&geohash=wydm7"
        ]
        
        for endpoint in price_endpoints:
            try:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Price data: {type(data)} - {len(data) if isinstance(data, list) else 'dict'}")
                        
                        if isinstance(data, list):
                            for item in data[:max_items//2]:
                                prop = self._parse_price_data(item)
                                if prop:
                                    properties.append(prop)
                        elif isinstance(data, dict) and 'data' in data:
                            for item in data['data'][:max_items//2]:
                                prop = self._parse_price_data(item)
                                if prop:
                                    properties.append(prop)
                                    
                        await asyncio.sleep(1)
                        
            except Exception as e:
                logger.error(f"Error collecting price data: {e}")
                
        return properties
    
    def _parse_apartment_marker(self, data):
        """아파트 마커 데이터 파싱"""
        try:
            return {
                'id': f"ZIGBANG_APT_{data.get('id', '')}",
                'platform': 'zigbang',
                'type': '아파트',
                'title': data.get('name', ''),
                'address': data.get('address', ''),
                'price': data.get('price', 0),
                'area': data.get('area', 0),
                'floor': data.get('floor', ''),
                'lat': data.get('lat'),
                'lng': data.get('lng'),
                'description': data.get('description', ''),
                'collected_at': datetime.now().isoformat(),
                'url': f"https://www.zigbang.com/apartment/{data.get('id', '')}",
                'raw_data': data
            }
        except Exception as e:
            logger.error(f"Error parsing apartment marker: {e}")
            return None
    
    def _parse_room_item(self, data):
        """원룸/오피스텔 아이템 파싱"""
        try:
            return {
                'id': f"ZIGBANG_ROOM_{data.get('item_id', '')}",
                'platform': 'zigbang',
                'type': data.get('room_type_str', '원룸'),
                'title': data.get('title', ''),
                'address': data.get('address', ''),
                'price': data.get('deposit', 0),
                'monthly_rent': data.get('rent', 0),
                'area': data.get('size_m2', 0),
                'floor': f"{data.get('floor', '')}층",
                'lat': data.get('lat'),
                'lng': data.get('lng'),
                'description': data.get('description', ''),
                'collected_at': datetime.now().isoformat(),
                'url': f"https://www.zigbang.com/room/{data.get('item_id', '')}",
                'raw_data': data
            }
        except Exception as e:
            logger.error(f"Error parsing room item: {e}")
            return None
    
    def _parse_price_data(self, data):
        """가격 데이터 파싱"""
        try:
            return {
                'id': f"ZIGBANG_PRICE_{data.get('complex_id', '')}{data.get('date', '')}",
                'platform': 'zigbang',
                'type': '아파트',
                'title': data.get('complex_name', ''),
                'address': data.get('address', ''),
                'price': data.get('price', 0),
                'area': data.get('area', 0),
                'floor': '',
                'lat': data.get('lat'),
                'lng': data.get('lng'),
                'description': f"거래일: {data.get('date', '')}",
                'collected_at': datetime.now().isoformat(),
                'url': f"https://www.zigbang.com/apartment/{data.get('complex_id', '')}",
                'raw_data': data
            }
        except Exception as e:
            logger.error(f"Error parsing price data: {e}")
            return None


async def main():
    """메인 실행 함수"""
    logger.info("🏠 직방 실제 API 삼성1동 매물 수집 시작")
    
    collector = ZigbangRealCollector()
    
    # 매물 수집
    properties = await collector.collect_samsung1dong(max_items=2000)
    
    # 결과 저장
    if properties:
        result = {
            'area': '강남구 삼성1동',
            'platform': 'zigbang',
            'collection_time': datetime.now().isoformat(),
            'total_properties': len(properties),
            'by_type': {},
            'properties': properties
        }
        
        # 타입별 집계
        for prop in properties:
            prop_type = prop.get('type', '기타')
            result['by_type'][prop_type] = result['by_type'].get(prop_type, 0) + 1
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'zigbang_samsung1dong_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ {len(properties)}개 매물 수집 완료 - {filename}")
        logger.info(f"📊 타입별 통계: {result['by_type']}")
        
        # 샘플 출력
        logger.info("🏠 샘플 매물:")
        for i, prop in enumerate(properties[:5]):
            logger.info(f"{i+1}. {prop.get('title', 'N/A')} - {prop.get('price', 0):,}만원 ({prop.get('type', 'N/A')})")
    else:
        logger.warning("❌ 수집된 매물이 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())