"""
베이스 수집기 클래스 - 모든 플랫폼 수집기의 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import asyncio
import aiohttp
from datetime import datetime
from loguru import logger
import random


class BaseCollector(ABC):
    """베이스 수집기 추상 클래스"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit = 2  # requests per second
        self.max_retries = 3
        self.headers = {
            'User-Agent': self._get_random_user_agent()
        }
        
    def _get_random_user_agent(self) -> str:
        """랜덤 User-Agent 반환"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        return random.choice(user_agents)
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
            
    @abstractmethod
    async def collect(self, area: str, **kwargs) -> List[Dict]:
        """
        매물 수집 메서드 (하위 클래스에서 구현)
        
        Args:
            area: 수집할 지역
            **kwargs: 추가 파라미터
            
        Returns:
            수집된 매물 정보 리스트
        """
        pass
        
    @abstractmethod
    async def parse_property(self, data: Dict) -> Dict:
        """
        매물 데이터 파싱 (하위 클래스에서 구현)
        
        Args:
            data: 원본 데이터
            
        Returns:
            정규화된 매물 정보
        """
        pass
        
    async def fetch(self, url: str, method: str = 'GET', 
                   **kwargs) -> Optional[Dict]:
        """
        HTTP 요청 실행
        
        Args:
            url: 요청 URL
            method: HTTP 메서드
            **kwargs: 추가 요청 파라미터
            
        Returns:
            응답 데이터 또는 None
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
            
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                await self._rate_limit()
                
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'json' in content_type:
                            return await response.json()
                        else:
                            return {'text': await response.text()}
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except Exception as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
        
    async def _rate_limit(self):
        """Rate limiting 적용"""
        await asyncio.sleep(1 / self.rate_limit)
        
    def normalize_price(self, price_str: str) -> Optional[int]:
        """
        가격 문자열을 정수로 변환
        
        Args:
            price_str: 가격 문자열 (예: "3억 5,000", "35000")
            
        Returns:
            만원 단위 정수 가격
        """
        if not price_str:
            return None
            
        try:
            # 문자열 정리
            price_str = price_str.replace(',', '').replace(' ', '')
            
            # 억 단위 처리
            if '억' in price_str:
                parts = price_str.split('억')
                eok = int(parts[0]) * 10000
                
                # 만원 단위 처리
                man = 0
                if len(parts) > 1 and parts[1]:
                    man_str = parts[1].replace('만', '').replace('원', '')
                    if man_str:
                        man = int(man_str)
                        
                return eok + man
                
            # 만원 단위만 있는 경우
            elif '만' in price_str:
                return int(price_str.replace('만', '').replace('원', ''))
                
            # 숫자만 있는 경우
            else:
                return int(price_str)
                
        except Exception as e:
            logger.error(f"Price parsing error: {price_str} - {e}")
            return None
            
    def normalize_area(self, area_str: str) -> Optional[float]:
        """
        면적 문자열을 float로 변환
        
        Args:
            area_str: 면적 문자열 (예: "84.95㎡", "25평")
            
        Returns:
            제곱미터 단위 면적
        """
        if not area_str:
            return None
            
        try:
            # 문자열 정리
            area_str = area_str.replace(' ', '')
            
            # 제곱미터 단위
            if '㎡' in area_str or 'm²' in area_str:
                return float(area_str.replace('㎡', '').replace('m²', ''))
                
            # 평 단위 (평 -> 제곱미터 변환)
            elif '평' in area_str:
                pyeong = float(area_str.replace('평', ''))
                return pyeong * 3.3058  # 1평 = 3.3058㎡
                
            # 숫자만 있는 경우 (제곱미터로 가정)
            else:
                return float(area_str)
                
        except Exception as e:
            logger.error(f"Area parsing error: {area_str} - {e}")
            return None
            
    def create_property_id(self, platform: str, original_id: str) -> str:
        """
        플랫폼별 고유 ID 생성
        
        Args:
            platform: 플랫폼 이름
            original_id: 원본 ID
            
        Returns:
            고유 ID
        """
        return f"{platform.upper()}_{original_id}"
        
    def validate_property(self, property_data: Dict) -> bool:
        """
        매물 데이터 유효성 검증
        
        Args:
            property_data: 매물 데이터
            
        Returns:
            유효 여부
        """
        required_fields = ['id', 'title', 'price', 'area', 'address']
        
        for field in required_fields:
            if field not in property_data or property_data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
                
        # 가격 범위 검증 (1000만원 ~ 500억원)
        price = property_data.get('price', 0)
        if price < 1000 or price > 5000000:
            logger.warning(f"Invalid price: {price}")
            return False
            
        # 면적 범위 검증 (10㎡ ~ 1000㎡)
        area = property_data.get('area', 0)
        if area < 10 or area > 1000:
            logger.warning(f"Invalid area: {area}")
            return False
            
        return True