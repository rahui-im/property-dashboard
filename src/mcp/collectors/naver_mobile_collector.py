"""
네이버 부동산 모바일 크롤러
매물 유형별 수집 지원 (아파트, 오피스텔, 빌라, 전원주택 등)
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, parse_qs

logger = logging.getLogger(__name__)


class PropertyType(Enum):
    """매물 유형 정의 - 총 18개"""
    # 1행 (6개)
    APT = "아파트"  # A1
    OFFICETEL = "오피스텔"  # B1
    VILLA = "빌라"  # B2
    APT_PRESALE = "아파트분양권"  # A2
    OFFICETEL_PRESALE = "오피스텔분양권"  # B3
    REDEVELOPMENT = "재건축"  # C4
    
    # 2행 (6개)
    TOWNHOUSE = "전원주택"  # C2
    DETACHED = "단독/다가구"  # C1
    RETAIL_HOUSE = "상가주택"  # C3
    HANOK = "한옥주택"  # H1
    RECONSTRUCTION = "재개발"  # D2
    ONEROOM = "원룸"  # I1
    
    # 3행 (6개)
    RETAIL = "상가"  # D1
    OFFICE = "사무실"  # E1
    WAREHOUSE = "공장/창고"  # F1
    LAND = "토지"  # G1
    KNOWLEDGE_CENTER = "지식산업센터"  # K1
    ACCOMMODATION = "숙박/펜션"  # J1


class TradeType(Enum):
    """거래 유형"""
    SALE = "매매"
    RENT = "전세"
    MONTHLY = "월세"
    SHORT = "단기"


class NaverMobileCollector:
    """네이버 부동산 모바일 크롤러"""
    
    BASE_URL = "https://m.land.naver.com"
    CLUSTER_API = "https://m.land.naver.com/cluster/clusterList"
    ARTICLE_API = "https://m.land.naver.com/cluster/ajax/articleList"
    
    # 매물 유형별 필터 코드 매핑
    PROPERTY_TYPE_CODES = {
        PropertyType.APT: "A1",
        PropertyType.OFFICETEL: "B1",
        PropertyType.VILLA: "B2",
        PropertyType.APT_PRESALE: "A2",
        PropertyType.OFFICETEL_PRESALE: "B3",
        PropertyType.REDEVELOPMENT: "C4",
        PropertyType.TOWNHOUSE: "C2",
        PropertyType.DETACHED: "C1",
        PropertyType.RETAIL_HOUSE: "C3",
        PropertyType.HANOK: "H1",
        PropertyType.RECONSTRUCTION: "D2",
        PropertyType.ONEROOM: "I1",
        PropertyType.RETAIL: "D1",
        PropertyType.OFFICE: "E1",
        PropertyType.WAREHOUSE: "F1",
        PropertyType.LAND: "G1",
        PropertyType.KNOWLEDGE_CENTER: "K1",
        PropertyType.ACCOMMODATION: "J1"
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://m.land.naver.com/'
        }
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
            
    async def search_area(
        self, 
        area: str,
        property_types: List[PropertyType] = None,
        trade_type: TradeType = TradeType.SALE
    ) -> Dict[str, Any]:
        """지역별 매물 검색
        
        Args:
            area: 검색할 지역명 (예: "강남구", "서초구")
            property_types: 검색할 매물 유형 리스트
            trade_type: 거래 유형 (매매/전세/월세)
            
        Returns:
            검색 결과 딕셔너리
        """
        if not property_types:
            property_types = [PropertyType.APT, PropertyType.OFFICETEL, PropertyType.VILLA]
            
        results = {
            "area": area,
            "trade_type": trade_type.value,
            "search_time": datetime.now().isoformat(),
            "properties": []
        }
        
        for prop_type in property_types:
            logger.info(f"Searching {prop_type.value} in {area}")
            try:
                properties = await self._search_by_type(area, prop_type, trade_type)
                results["properties"].extend(properties)
                logger.info(f"Found {len(properties)} {prop_type.value} properties")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching {prop_type.value}: {e}")
                continue
                
        return results
        
    async def _search_by_type(
        self,
        area: str,
        property_type: PropertyType,
        trade_type: TradeType
    ) -> List[Dict[str, Any]]:
        """매물 유형별 검색
        
        Args:
            area: 지역명
            property_type: 매물 유형
            trade_type: 거래 유형
            
        Returns:
            매물 리스트
        """
        # 좌표 검색
        lat, lng = await self._get_coordinates(area)
        
        # 매물 유형에 따라 적절한 코드 사용
        if property_type == PropertyType.APT:
            type_code = "APT"
        elif property_type == PropertyType.OFFICETEL:
            type_code = "OPST"
        elif property_type == PropertyType.VILLA:
            type_code = "VL"
        else:
            type_code = "APT"  # 기본값
        
        # API 파라미터 구성
        params = {
            "rletTpCd": type_code,
            "tradTpCd": self._get_trade_code(trade_type),
            "z": "13",  # 줌 레벨
            "lat": str(lat),
            "lon": str(lng),
            "btm": str(lat - 0.01),
            "lft": str(lng - 0.01),
            "top": str(lat + 0.01),
            "rgt": str(lng + 0.01),
            "cortarNo": "",
            "page": "1"
        }
        
        properties = []
        
        try:
            # 개별 매물 정보 가져오기
            async with self.session.get(
                self.ARTICLE_API,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 매물 리스트 확인
                    if "body" in data and isinstance(data["body"], list):
                        for article in data["body"]:
                            property_info = self._parse_article(article, property_type)
                            if property_info:
                                properties.append(property_info)
                                
                    logger.info(f"Found {len(properties)} properties for {property_type.value}")
                else:
                    logger.warning(f"API returned status {response.status}")
                                
        except Exception as e:
            logger.error(f"Error fetching properties: {e}")
            
        return properties
        
    async def _parse_complex(
        self,
        complex_data: Dict,
        property_type: PropertyType
    ) -> Optional[Dict[str, Any]]:
        """아파트/오피스텔 단지 정보 파싱
        
        Args:
            complex_data: 단지 데이터
            property_type: 매물 유형
            
        Returns:
            파싱된 매물 정보
        """
        try:
            return {
                "type": property_type.value,
                "complex_id": complex_data.get("lgeo", ""),
                "name": complex_data.get("markTitle", ""),
                "address": complex_data.get("juso", ""),
                "count": complex_data.get("dealCnt", 0),
                "min_price": complex_data.get("minPrc", 0),
                "max_price": complex_data.get("maxPrc", 0),
                "lat": complex_data.get("lat", 0),
                "lon": complex_data.get("lon", 0),
                "collected_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing complex: {e}")
            return None
            
    def _parse_article(
        self,
        article_data: Dict,
        property_type: PropertyType
    ) -> Optional[Dict[str, Any]]:
        """개별 매물 정보 파싱
        
        Args:
            article_data: 매물 데이터
            property_type: 매물 유형
            
        Returns:
            파싱된 매물 정보
        """
        try:
            # 가격 처리 (문자열로 올 수 있음)
            price = article_data.get("prc", "0")
            if isinstance(price, str):
                price = int(price.replace(",", "")) if price else 0
            
            # 면적 처리
            area = article_data.get("spc1", article_data.get("spc", "0"))
            if isinstance(area, str):
                area = float(area) if area else 0
                
            return {
                "type": property_type.value,
                "article_id": str(article_data.get("atclNo", "")),
                "title": article_data.get("atclNm", ""),
                "address": article_data.get("cortarNm", ""),  # cortarNm이 주소
                "price": price,
                "area": area,
                "floor": article_data.get("flrInfo", ""),
                "direction": article_data.get("direction", ""),
                "lat": article_data.get("lat", 0),
                "lon": article_data.get("lng", article_data.get("lon", 0)),
                "realtor": article_data.get("rltrNm", ""),
                "description": article_data.get("atclFetrDesc", ""),
                "collected_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing article: {e}")
            return None
            
    async def _get_coordinates(self, area: str) -> tuple:
        """지역명으로 좌표 검색
        
        Args:
            area: 지역명
            
        Returns:
            (위도, 경도) 튜플
        """
        # 주요 지역 좌표 (실제로는 API나 DB에서 가져와야 함)
        AREA_COORDS = {
            "강남구": (37.5172, 127.0473),
            "서초구": (37.4837, 127.0324),
            "송파구": (37.5145, 127.1059),
            "강동구": (37.5301, 127.1238),
            "마포구": (37.5663, 126.9019),
            "용산구": (37.5324, 126.9905),
            "성동구": (37.5634, 127.0371),
            "광진구": (37.5384, 127.0823),
            "중구": (37.5640, 126.9979),
            "종로구": (37.5735, 126.9790)
        }
        
        return AREA_COORDS.get(area, (37.5665, 126.9780))  # 기본값: 서울시청
        
    def _get_trade_code(self, trade_type: TradeType) -> str:
        """거래 유형 코드 변환
        
        Args:
            trade_type: 거래 유형
            
        Returns:
            거래 코드
        """
        trade_codes = {
            TradeType.SALE: "A1",    # 매매
            TradeType.RENT: "B1",    # 전세
            TradeType.MONTHLY: "B2",  # 월세
            TradeType.SHORT: "B3"    # 단기
        }
        return trade_codes.get(trade_type, "A1")
        
    async def get_property_detail(self, property_id: str, property_type: PropertyType) -> Dict[str, Any]:
        """매물 상세 정보 조회
        
        Args:
            property_id: 매물 ID
            property_type: 매물 유형
            
        Returns:
            상세 정보 딕셔너리
        """
        # TODO: 상세 정보 API 구현
        pass


async def main():
    """테스트 실행"""
    async with NaverMobileCollector() as collector:
        # 강남구 아파트, 오피스텔, 빌라 검색
        results = await collector.search_area(
            area="강남구",
            property_types=[
                PropertyType.APT,
                PropertyType.OFFICETEL,
                PropertyType.VILLA
            ],
            trade_type=TradeType.SALE
        )
        
        print(f"총 {len(results['properties'])}개 매물 발견")
        for prop in results['properties'][:5]:  # 상위 5개만 출력
            print(f"- {prop.get('type')}: {prop.get('name', prop.get('title'))} - {prop.get('price', prop.get('min_price'))}만원")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())