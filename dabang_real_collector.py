#!/usr/bin/env python3
"""
실제 다방 API를 사용한 삼성1동 매물 수집기
다방 웹사이트 분석을 통해 실제 API를 사용합니다.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from loguru import logger
import sys

# 한글 출력 설정
sys.stdout.reconfigure(encoding='utf-8')


class DabangRealCollector:
    """실제 다방 API를 사용한 수집기"""
    
    def __init__(self):
        self.base_url = "https://www.dabangapp.com"
        self.api_url = "https://api.dabangapp.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Origin': 'https://www.dabangapp.com',
            'Referer': 'https://www.dabangapp.com/'
        }
        
        # 삼성1동 좌표 정보
        self.samsung1dong_coords = {
            'lat': 37.518,
            'lng': 127.048,
            'bounds': {
                'lat_min': 37.508,
                'lat_max': 37.528,
                'lng_min': 37.038,
                'lng_max': 127.058
            }
        }
        
    async def collect_samsung1dong(self, max_items=2000):
        """삼성1동 매물 수집"""
        properties = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            
            # 1. 원룸/오피스텔 수집
            room_properties = await self._collect_rooms(session, max_items // 2)
            properties.extend(room_properties)
            
            # 2. 아파트 수집  
            apt_properties = await self._collect_apartments(session, max_items // 4)
            properties.extend(apt_properties)
            
            # 3. 지역 검색으로 추가 수집
            search_properties = await self._collect_by_search(session, max_items // 4)
            properties.extend(search_properties)
            
        # 중복 제거
        unique_properties = self._remove_duplicates(properties)
        
        logger.info(f"Total collected: {len(unique_properties)} properties from Dabang")
        return unique_properties
    
    async def _collect_rooms(self, session, max_items):
        """원룸/오피스텔 수집"""
        properties = []
        
        # 다방의 실제 원룸 검색 API
        endpoints = [
            f"{self.api_url}/v5/rooms/list",
            f"{self.api_url}/v4/rooms/list", 
            f"{self.base_url}/api/3/room/list"
        ]
        
        for endpoint in endpoints:
            try:
                # 여러 조건으로 검색
                search_conditions = [
                    {  # 매매
                        'latitude': self.samsung1dong_coords['lat'],
                        'longitude': self.samsung1dong_coords['lng'],
                        'radius': 2000,
                        'selling_type': '매매',
                        'room_type': [1, 2, 3],  # 원룸, 투룸, 오피스텔
                        'limit': 100
                    },
                    {  # 전세
                        'latitude': self.samsung1dong_coords['lat'],
                        'longitude': self.samsung1dong_coords['lng'],
                        'radius': 2000,
                        'selling_type': '전세',
                        'room_type': [1, 2, 3],
                        'limit': 100
                    },
                    {  # 월세
                        'latitude': self.samsung1dong_coords['lat'],
                        'longitude': self.samsung1dong_coords['lng'],
                        'radius': 2000,
                        'selling_type': '월세',
                        'room_type': [1, 2, 3],
                        'limit': 100
                    }
                ]
                
                for condition in search_conditions:
                    try:
                        async with session.get(endpoint, params=condition) as response:
                            if response.status == 200:
                                content_type = response.headers.get('Content-Type', '')
                                
                                if 'json' in content_type:
                                    data = await response.json()
                                    logger.info(f"✅ Room data from {endpoint}: {type(data)}")
                                    
                                    rooms = []
                                    if isinstance(data, dict):
                                        rooms = data.get('rooms', data.get('result', data.get('items', [])))
                                    elif isinstance(data, list):
                                        rooms = data
                                    
                                    for room in rooms[:max_items//6]:
                                        prop = self._parse_room(room)
                                        if prop and self._is_in_samsung1dong(prop):
                                            properties.append(prop)
                                            
                                    logger.info(f"Collected {len(rooms)} rooms from condition {condition['selling_type']}")
                                    await asyncio.sleep(1)
                                    
                            else:
                                logger.warning(f"HTTP {response.status} for {endpoint}")
                                
                    except Exception as e:
                        logger.debug(f"Error with condition {condition}: {e}")
                        
                if properties:  # 성공한 엔드포인트가 있으면 다른 것은 시도하지 않음
                    break
                    
            except Exception as e:
                logger.error(f"Error collecting rooms from {endpoint}: {e}")
                
        return properties[:max_items]
    
    async def _collect_apartments(self, session, max_items):
        """아파트 수집"""
        properties = []
        
        # 다방 아파트 API 엔드포인트들
        endpoints = [
            f"{self.api_url}/v1/apartments/list",
            f"{self.base_url}/api/3/apartment/list",
            f"{self.api_url}/v2/apartments"
        ]
        
        for endpoint in endpoints:
            try:
                params = {
                    'region': '강남구',
                    'dong': '삼성1동',
                    'sales_type': '매매',
                    'limit': max_items
                }
                
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'json' in content_type:
                            data = await response.json()
                            logger.info(f"✅ Apartment data from {endpoint}: {type(data)}")
                            
                            apartments = []
                            if isinstance(data, dict):
                                apartments = data.get('apartments', data.get('result', data.get('items', [])))
                            elif isinstance(data, list):
                                apartments = data
                            
                            for apt in apartments[:max_items]:
                                prop = self._parse_apartment(apt)
                                if prop and self._is_in_samsung1dong(prop):
                                    properties.append(prop)
                                    
                            if apartments:
                                break  # 성공하면 다른 엔드포인트 시도하지 않음
                                
            except Exception as e:
                logger.error(f"Error collecting apartments from {endpoint}: {e}")
                
        return properties
    
    async def _collect_by_search(self, session, max_items):
        """지역 검색으로 추가 수집"""
        properties = []
        
        # 검색 API
        search_endpoints = [
            f"{self.api_url}/v1/search",
            f"{self.base_url}/api/search",
            f"{self.api_url}/v2/search/rooms"
        ]
        
        search_terms = ['강남구 삼성1동', '삼성1동', '강남구']
        
        for endpoint in search_endpoints:
            for term in search_terms:
                try:
                    params = {
                        'q': term,
                        'type': 'room',
                        'limit': max_items // len(search_terms)
                    }
                    
                    async with session.get(endpoint, params=params) as response:
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            
                            if 'json' in content_type:
                                data = await response.json()
                                logger.info(f"✅ Search data for '{term}': {type(data)}")
                                
                                items = []
                                if isinstance(data, dict):
                                    items = data.get('rooms', data.get('result', data.get('items', [])))
                                elif isinstance(data, list):
                                    items = data
                                
                                for item in items:
                                    prop = self._parse_search_result(item)
                                    if prop and self._is_in_samsung1dong(prop):
                                        properties.append(prop)
                                        
                                await asyncio.sleep(1)
                                
                except Exception as e:
                    logger.debug(f"Error searching '{term}' at {endpoint}: {e}")
                    
        return properties
    
    def _parse_room(self, data):
        """원룸/오피스텔 데이터 파싱"""
        try:
            room_id = data.get('room_id', data.get('id', ''))
            
            return {
                'id': f"DABANG_ROOM_{room_id}",
                'platform': 'dabang',
                'type': data.get('room_type_str', data.get('room_type', '원룸')),
                'title': data.get('title', data.get('name', '')),
                'address': data.get('address', ''),
                'price': data.get('deposit', data.get('price', 0)),
                'monthly_rent': data.get('rent', data.get('monthly_rent', 0)),
                'area': data.get('area', data.get('size_m2', 0)),
                'floor': f"{data.get('floor', '')}층",
                'lat': data.get('latitude', data.get('lat')),
                'lng': data.get('longitude', data.get('lng')),
                'description': data.get('desc', data.get('description', '')),
                'collected_at': datetime.now().isoformat(),
                'url': f"https://www.dabangapp.com/room/{room_id}",
                'trade_type': data.get('selling_type', ''),
                'raw_data': data
            }
        except Exception as e:
            logger.error(f"Error parsing room: {e}")
            return None
    
    def _parse_apartment(self, data):
        """아파트 데이터 파싱"""
        try:
            apt_id = data.get('apartment_id', data.get('id', ''))
            
            return {
                'id': f"DABANG_APT_{apt_id}",
                'platform': 'dabang',
                'type': '아파트',
                'title': data.get('name', data.get('title', '')),
                'address': data.get('address', ''),
                'price': data.get('price', 0),
                'area': data.get('area', 0),
                'floor': data.get('floor_string', ''),
                'lat': data.get('latitude', data.get('lat')),
                'lng': data.get('longitude', data.get('lng')),
                'description': data.get('description', ''),
                'collected_at': datetime.now().isoformat(),
                'url': f"https://www.dabangapp.com/apartment/{apt_id}",
                'trade_type': data.get('selling_type', '매매'),
                'raw_data': data
            }
        except Exception as e:
            logger.error(f"Error parsing apartment: {e}")
            return None
    
    def _parse_search_result(self, data):
        """검색 결과 파싱"""
        try:
            item_id = data.get('id', data.get('room_id', ''))
            
            return {
                'id': f"DABANG_SEARCH_{item_id}",
                'platform': 'dabang',
                'type': data.get('type', data.get('room_type_str', '기타')),
                'title': data.get('title', data.get('name', '')),
                'address': data.get('address', ''),
                'price': data.get('price', data.get('deposit', 0)),
                'area': data.get('area', 0),
                'floor': data.get('floor_string', ''),
                'lat': data.get('lat', data.get('latitude')),
                'lng': data.get('lng', data.get('longitude')),
                'description': data.get('description', ''),
                'collected_at': datetime.now().isoformat(),
                'url': f"https://www.dabangapp.com/room/{item_id}",
                'raw_data': data
            }
        except Exception as e:
            logger.error(f"Error parsing search result: {e}")
            return None
    
    def _is_in_samsung1dong(self, prop):
        """삼성1동 지역 내 매물인지 확인"""
        try:
            lat = prop.get('lat')
            lng = prop.get('lng')
            address = prop.get('address', '')
            
            # 주소에 삼성1동이 포함되어 있으면 OK
            if '삼성1동' in address or '삼성동' in address:
                return True
            
            # 좌표 범위 확인
            if lat and lng:
                bounds = self.samsung1dong_coords['bounds']
                if (bounds['lat_min'] <= lat <= bounds['lat_max'] and 
                    bounds['lng_min'] <= lng <= bounds['lng_max']):
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _remove_duplicates(self, properties):
        """중복 매물 제거"""
        seen = set()
        unique_properties = []
        
        for prop in properties:
            # 제목, 주소, 가격으로 중복 판단
            key = (prop.get('title', ''), prop.get('address', ''), prop.get('price', 0))
            
            if key not in seen:
                seen.add(key)
                unique_properties.append(prop)
                
        logger.info(f"Removed {len(properties) - len(unique_properties)} duplicates")
        return unique_properties


async def main():
    """메인 실행 함수"""
    logger.info("🏠 다방 실제 API 삼성1동 매물 수집 시작")
    
    collector = DabangRealCollector()
    
    # 매물 수집
    properties = await collector.collect_samsung1dong(max_items=2000)
    
    # 결과 저장
    if properties:
        result = {
            'area': '강남구 삼성1동',
            'platform': 'dabang',
            'collection_time': datetime.now().isoformat(),
            'total_properties': len(properties),
            'by_type': {},
            'by_trade': {},
            'properties': properties
        }
        
        # 타입별, 거래별 집계
        for prop in properties:
            prop_type = prop.get('type', '기타')
            trade_type = prop.get('trade_type', '기타')
            
            result['by_type'][prop_type] = result['by_type'].get(prop_type, 0) + 1
            result['by_trade'][trade_type] = result['by_trade'].get(trade_type, 0) + 1
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'dabang_samsung1dong_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ {len(properties)}개 매물 수집 완료 - {filename}")
        logger.info(f"📊 타입별 통계: {result['by_type']}")
        logger.info(f"📊 거래별 통계: {result['by_trade']}")
        
        # 샘플 출력
        logger.info("🏠 샘플 매물:")
        for i, prop in enumerate(properties[:5]):
            logger.info(f"{i+1}. {prop.get('title', 'N/A')} - {prop.get('price', 0):,}만원 ({prop.get('type', 'N/A')})")
    else:
        logger.warning("❌ 수집된 매물이 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())