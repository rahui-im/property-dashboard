#!/usr/bin/env python3
"""
멀티플랫폼 부동산 데이터 통합 시스템
네이버, 직방, 다방, KB부동산 등의 데이터를 정규화하고 중복을 제거합니다.
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Set
from loguru import logger
import sys
import os
from dataclasses import dataclass
from difflib import SequenceMatcher

# 한글 출력 설정
sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class PropertyData:
    """표준화된 매물 데이터 클래스"""
    id: str
    platform: str
    type: str
    title: str
    address: str
    price: int
    area: float
    floor: str
    lat: float = None
    lng: float = None
    description: str = ""
    trade_type: str = "매매"
    monthly_rent: int = 0
    collected_at: str = ""
    url: str = ""
    raw_data: dict = None


class DataIntegrationSystem:
    """데이터 통합 시스템"""
    
    def __init__(self):
        self.supported_platforms = ['naver', 'zigbang', 'dabang', 'kb']
        self.duplicate_threshold = 0.85  # 중복 판단 임계값
        
    def integrate_all_platforms(self, target_area="강남구 삼성1동", max_per_platform=2000):
        """모든 플랫폼 데이터 통합"""
        logger.info(f"🏠 멀티플랫폼 데이터 통합 시작 - {target_area}")
        
        all_properties = []
        platform_stats = {}
        
        # 1. 각 플랫폼별 데이터 로드
        for platform in self.supported_platforms:
            properties = self._load_platform_data(platform, target_area)
            
            if properties:
                platform_stats[platform] = len(properties)
                all_properties.extend(properties)
                logger.info(f"✅ {platform}: {len(properties)}개 매물 로드")
            else:
                platform_stats[platform] = 0
                logger.warning(f"❌ {platform}: 데이터 없음")
        
        logger.info(f"📊 총 {len(all_properties)}개 매물 로드 완료")
        
        # 2. 데이터 정규화
        normalized_properties = self._normalize_all_data(all_properties)
        logger.info(f"✅ 데이터 정규화 완료: {len(normalized_properties)}개")
        
        # 3. 중복 제거
        unique_properties = self._remove_duplicates(normalized_properties)
        logger.info(f"✅ 중복 제거 완료: {len(unique_properties)}개 (제거: {len(normalized_properties) - len(unique_properties)}개)")
        
        # 4. 통계 분석
        statistics = self._analyze_statistics(unique_properties, platform_stats)
        
        # 5. 결과 반환
        return {
            'area': target_area,
            'integration_time': datetime.now().isoformat(),
            'total_properties': len(unique_properties),
            'platform_stats': platform_stats,
            'statistics': statistics,
            'properties': unique_properties
        }
    
    def _load_platform_data(self, platform, target_area):
        """플랫폼별 데이터 로드"""
        properties = []
        
        try:
            # 플랫폼별 최신 파일 찾기
            files = [f for f in os.listdir('.') if f.startswith(f'{platform}_') and f.endswith('.json')]
            
            if not files:
                logger.warning(f"No {platform} data files found")
                return properties
            
            # 가장 최신 파일 선택
            latest_file = max(files, key=lambda x: os.path.getmtime(x))
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict) and 'properties' in data:
                raw_properties = data['properties']
            elif isinstance(data, list):
                raw_properties = data
            else:
                logger.warning(f"Invalid data format in {latest_file}")
                return properties
            
            # 플랫폼별 파싱
            for prop in raw_properties:
                normalized = self._normalize_property(prop, platform)
                if normalized:
                    properties.append(normalized)
                    
            logger.info(f"Loaded {len(properties)} properties from {latest_file}")
            
        except Exception as e:
            logger.error(f"Error loading {platform} data: {e}")
            
        return properties
    
    def _normalize_property(self, prop, platform):
        """개별 매물 데이터 정규화"""
        try:
            # 플랫폼별 매핑
            if platform == 'naver':
                return self._normalize_naver(prop)
            elif platform == 'zigbang':
                return self._normalize_zigbang(prop)
            elif platform == 'dabang':
                return self._normalize_dabang(prop)
            elif platform == 'kb':
                return self._normalize_kb(prop)
            else:
                return self._normalize_generic(prop, platform)
                
        except Exception as e:
            logger.debug(f"Error normalizing {platform} property: {e}")
            return None
    
    def _normalize_naver(self, prop):
        """네이버 데이터 정규화"""
        return PropertyData(
            id=f"NAVER_{prop.get('article_id', '')}",
            platform='naver',
            type=prop.get('type', '기타'),
            title=prop.get('title', ''),
            address=prop.get('address', ''),
            price=prop.get('price', 0),
            area=prop.get('area', 0),
            floor=prop.get('floor', ''),
            lat=prop.get('lat'),
            lng=prop.get('lon'),
            description=prop.get('description', ''),
            trade_type=prop.get('trade_type', '매매'),
            collected_at=prop.get('collected_at', ''),
            url=prop.get('naver_link', ''),
            raw_data=prop
        )
    
    def _normalize_zigbang(self, prop):
        """직방 데이터 정규화"""
        return PropertyData(
            id=prop.get('id', f"ZIGBANG_{hash(str(prop))}"),
            platform='zigbang',
            type=prop.get('type', '기타'),
            title=prop.get('title', ''),
            address=prop.get('address', ''),
            price=prop.get('price', 0),
            area=prop.get('area', 0),
            floor=prop.get('floor', ''),
            lat=prop.get('lat'),
            lng=prop.get('lng'),
            description=prop.get('description', ''),
            monthly_rent=prop.get('monthly_rent', 0),
            collected_at=prop.get('collected_at', ''),
            url=prop.get('url', ''),
            raw_data=prop
        )
    
    def _normalize_dabang(self, prop):
        """다방 데이터 정규화"""
        return PropertyData(
            id=prop.get('id', f"DABANG_{hash(str(prop))}"),
            platform='dabang',
            type=prop.get('type', '기타'),
            title=prop.get('title', ''),
            address=prop.get('address', ''),
            price=prop.get('price', 0),
            area=prop.get('area', 0),
            floor=prop.get('floor', ''),
            lat=prop.get('lat'),
            lng=prop.get('lng'),
            description=prop.get('description', ''),
            trade_type=prop.get('trade_type', '매매'),
            monthly_rent=prop.get('monthly_rent', 0),
            collected_at=prop.get('collected_at', ''),
            url=prop.get('url', ''),
            raw_data=prop
        )
    
    def _normalize_kb(self, prop):
        """KB부동산 데이터 정규화"""
        return PropertyData(
            id=prop.get('id', f"KB_{hash(str(prop))}"),
            platform='kb',
            type=prop.get('type', '기타'),
            title=prop.get('title', ''),
            address=prop.get('address', ''),
            price=prop.get('price', 0),
            area=prop.get('area', 0),
            floor=prop.get('floor', ''),
            description=prop.get('description', ''),
            collected_at=prop.get('collected_at', ''),
            url=prop.get('url', ''),
            raw_data=prop
        )
    
    def _normalize_generic(self, prop, platform):
        """일반적인 데이터 정규화"""
        return PropertyData(
            id=prop.get('id', f"{platform.upper()}_{hash(str(prop))}"),
            platform=platform,
            type=prop.get('type', '기타'),
            title=prop.get('title', ''),
            address=prop.get('address', ''),
            price=prop.get('price', 0),
            area=prop.get('area', 0),
            floor=prop.get('floor', ''),
            lat=prop.get('lat'),
            lng=prop.get('lng'),
            description=prop.get('description', ''),
            collected_at=prop.get('collected_at', ''),
            url=prop.get('url', ''),
            raw_data=prop
        )
    
    def _normalize_all_data(self, properties):
        """모든 데이터 정규화"""
        normalized = []
        
        for prop in properties:
            if isinstance(prop, PropertyData):
                normalized.append(prop)
            else:
                # 이미 dict 형태로 온 경우 PropertyData로 변환
                try:
                    prop_data = PropertyData(**prop)
                    normalized.append(prop_data)
                except Exception as e:
                    logger.debug(f"Error converting to PropertyData: {e}")
                    
        return normalized
    
    def _remove_duplicates(self, properties):
        """중복 매물 제거"""
        unique_properties = []
        seen_hashes = set()
        
        for prop in properties:
            # 중복 판단을 위한 해시 생성
            duplicate_hash = self._generate_duplicate_hash(prop)
            
            is_duplicate = False
            
            # 기존 매물과 유사도 비교
            for existing_prop in unique_properties:
                if self._is_duplicate(prop, existing_prop):
                    is_duplicate = True
                    # 더 정보가 많은 매물로 교체
                    if self._is_better_property(prop, existing_prop):
                        unique_properties.remove(existing_prop)
                        unique_properties.append(prop)
                    break
            
            if not is_duplicate and duplicate_hash not in seen_hashes:
                unique_properties.append(prop)
                seen_hashes.add(duplicate_hash)
        
        return unique_properties
    
    def _generate_duplicate_hash(self, prop):
        """중복 판단용 해시 생성"""
        # 제목, 주소, 가격, 면적으로 해시 생성
        hash_string = f"{prop.title}_{prop.address}_{prop.price}_{prop.area}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _is_duplicate(self, prop1, prop2):
        """두 매물이 중복인지 판단"""
        # 1. 제목 유사도
        title_similarity = SequenceMatcher(None, prop1.title, prop2.title).ratio()
        
        # 2. 주소 유사도
        address_similarity = SequenceMatcher(None, prop1.address, prop2.address).ratio()
        
        # 3. 가격 차이 (10% 이내)
        price_diff = abs(prop1.price - prop2.price) / max(prop1.price, prop2.price, 1)
        price_similarity = 1 - price_diff if price_diff < 0.1 else 0
        
        # 4. 면적 차이 (5% 이내)
        area_diff = abs(prop1.area - prop2.area) / max(prop1.area, prop2.area, 1)
        area_similarity = 1 - area_diff if area_diff < 0.05 else 0
        
        # 5. 좌표 거리 (있는 경우)
        coord_similarity = 0
        if prop1.lat and prop1.lng and prop2.lat and prop2.lng:
            distance = self._calculate_distance(prop1.lat, prop1.lng, prop2.lat, prop2.lng)
            coord_similarity = 1 if distance < 100 else 0  # 100m 이내
        
        # 가중 평균으로 최종 유사도 계산
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]
        similarities = [title_similarity, address_similarity, price_similarity, area_similarity, coord_similarity]
        
        total_similarity = sum(w * s for w, s in zip(weights, similarities))
        
        return total_similarity >= self.duplicate_threshold
    
    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """두 좌표 간 거리 계산 (미터)"""
        import math
        
        R = 6371000  # 지구 반지름 (미터)
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _is_better_property(self, prop1, prop2):
        """어느 매물이 더 정보가 풍부한지 판단"""
        score1 = self._calculate_info_score(prop1)
        score2 = self._calculate_info_score(prop2)
        
        return score1 > score2
    
    def _calculate_info_score(self, prop):
        """매물 정보 점수 계산"""
        score = 0
        
        if prop.title: score += 1
        if prop.address: score += 1
        if prop.price > 0: score += 1
        if prop.area > 0: score += 1
        if prop.lat and prop.lng: score += 2
        if prop.description: score += 1
        if prop.url: score += 1
        
        return score
    
    def _analyze_statistics(self, properties, platform_stats):
        """통계 분석"""
        stats = {
            'by_platform': platform_stats,
            'by_type': {},
            'by_trade': {},
            'by_price_range': {},
            'by_area_range': {},
            'price_stats': {},
            'area_stats': {}
        }
        
        if not properties:
            return stats
        
        # 타입별 통계
        for prop in properties:
            prop_type = prop.type
            trade_type = prop.trade_type
            
            stats['by_type'][prop_type] = stats['by_type'].get(prop_type, 0) + 1
            stats['by_trade'][trade_type] = stats['by_trade'].get(trade_type, 0) + 1
        
        # 가격 범위별 통계
        for prop in properties:
            price = prop.price
            if price <= 10000:
                range_key = "1억 이하"
            elif price <= 50000:
                range_key = "1억-5억"
            elif price <= 100000:
                range_key = "5억-10억"
            else:
                range_key = "10억 초과"
                
            stats['by_price_range'][range_key] = stats['by_price_range'].get(range_key, 0) + 1
        
        # 면적 범위별 통계
        for prop in properties:
            area = prop.area
            if area <= 40:
                range_key = "40㎡ 이하"
            elif area <= 60:
                range_key = "40-60㎡"
            elif area <= 85:
                range_key = "60-85㎡"
            else:
                range_key = "85㎡ 초과"
                
            stats['by_area_range'][range_key] = stats['by_area_range'].get(range_key, 0) + 1
        
        # 가격/면적 통계
        prices = [p.price for p in properties if p.price > 0]
        areas = [p.area for p in properties if p.area > 0]
        
        if prices:
            stats['price_stats'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices) // 2]
            }
        
        if areas:
            stats['area_stats'] = {
                'min': min(areas),
                'max': max(areas),
                'avg': sum(areas) / len(areas),
                'median': sorted(areas)[len(areas) // 2]
            }
        
        return stats
    
    def save_integrated_data(self, integrated_data, filename_prefix="integrated_samsung1dong"):
        """통합 데이터 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 파일 저장
        json_filename = f"{filename_prefix}_{timestamp}.json"
        
        # PropertyData 객체를 dict로 변환
        serializable_data = integrated_data.copy()
        serializable_data['properties'] = [
            {
                'id': prop.id,
                'platform': prop.platform,
                'type': prop.type,
                'title': prop.title,
                'address': prop.address,
                'price': prop.price,
                'area': prop.area,
                'floor': prop.floor,
                'lat': prop.lat,
                'lng': prop.lng,
                'description': prop.description,
                'trade_type': prop.trade_type,
                'monthly_rent': prop.monthly_rent,
                'collected_at': prop.collected_at,
                'url': prop.url
            }
            for prop in integrated_data['properties']
        ]
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 통합 데이터 저장 완료: {json_filename}")
        
        return json_filename


def main():
    """메인 함수"""
    logger.info("🏠 멀티플랫폼 부동산 데이터 통합 시스템 시작")
    
    # 통합 시스템 초기화
    integrator = DataIntegrationSystem()
    
    # 모든 플랫폼 데이터 통합
    integrated_data = integrator.integrate_all_platforms()
    
    # 결과 출력
    logger.info("📊 통합 결과:")
    logger.info(f"총 매물 수: {integrated_data['total_properties']:,}개")
    logger.info(f"플랫폼별 통계: {integrated_data['platform_stats']}")
    logger.info(f"타입별 통계: {integrated_data['statistics']['by_type']}")
    
    # 파일 저장
    filename = integrator.save_integrated_data(integrated_data)
    
    # 목표 달성 확인
    total = integrated_data['total_properties']
    target = 8000
    
    if total >= target:
        logger.info(f"🎉 목표 달성! {total:,}개 >= {target:,}개")
    else:
        logger.warning(f"❌ 목표 미달성: {total:,}개 < {target:,}개 (부족: {target - total:,}개)")
    
    return integrated_data


if __name__ == "__main__":
    main()