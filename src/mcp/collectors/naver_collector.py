"""
네이버 부동산 수집기
"""
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
from loguru import logger
from playwright.async_api import async_playwright
import json

from .base_collector import BaseCollector


class NaverCollector(BaseCollector):
    """네이버 부동산 수집기"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://land.naver.com"
        self.area_codes = {
            "강남구": "1168000000",
            "서초구": "1165000000",
            "송파구": "1171000000",
            "강동구": "1174000000",
            "강서구": "1150000000",
            "마포구": "1144000000",
            "용산구": "1117000000",
            "성동구": "1120000000",
            "광진구": "1121500000",
            "노원구": "1135000000",
            "중구": "1114000000",
            "종로구": "1111000000",
            "성북구": "1129000000",
            "동대문구": "1123000000",
            "중랑구": "1126000000",
            "도봉구": "1132000000",
            "은평구": "1138000000",
            "서대문구": "1141000000",
            "양천구": "1147000000",
            "구로구": "1153000000",
            "금천구": "1154500000",
            "영등포구": "1156000000",
            "동작구": "1159000000",
            "관악구": "1162000000",
            "강북구": "1130500000"
        }
        
    async def collect(self, area: str, property_type: str = "APT", 
                     trade_type: str = "A1", max_items: int = 100) -> List[Dict]:
        """
        네이버 부동산에서 매물 수집
        
        Args:
            area: 지역명 (예: "강남구")
            property_type: 매물 유형 (APT: 아파트, OPST: 오피스텔, VL: 빌라)
            trade_type: 거래 유형 (A1: 매매, B1: 전세, B2: 월세)
            max_items: 최대 수집 개수
            
        Returns:
            수집된 매물 리스트
        """
        if area not in self.area_codes:
            logger.warning(f"Unsupported area: {area}")
            return []
            
        properties = []
        area_code = self.area_codes[area]
        
        try:
            # Playwright를 사용한 동적 페이지 수집
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self._get_random_user_agent()
                )
                page = await context.new_page()
                
                # 매물 목록 페이지 접근
                url = f"{self.base_url}/article?cortarNo={area_code}&articleListYN=Y"
                await page.goto(url, wait_until='networkidle')
                
                # 필터 설정 (매물 유형, 거래 유형)
                await self._apply_filters(page, property_type, trade_type)
                
                # 매물 목록 수집
                collected = 0
                page_num = 1
                
                while collected < max_items:
                    # 현재 페이지의 매물 목록 가져오기
                    items = await self._extract_properties(page)
                    
                    for item in items:
                        if collected >= max_items:
                            break
                            
                        # 매물 상세 정보 수집
                        property_data = await self._get_property_detail(page, item)
                        if property_data:
                            # 데이터 정규화
                            normalized = await self.parse_property(property_data)
                            if self.validate_property(normalized):
                                properties.append(normalized)
                                collected += 1
                                
                    # 다음 페이지로 이동
                    has_next = await self._go_to_next_page(page)
                    if not has_next:
                        break
                        
                    page_num += 1
                    await asyncio.sleep(2)  # Rate limiting
                    
                await browser.close()
                
        except Exception as e:
            logger.error(f"Error collecting from Naver: {e}")
            
        logger.info(f"Collected {len(properties)} properties from Naver for {area}")
        return properties
        
    async def _apply_filters(self, page, property_type: str, trade_type: str):
        """필터 적용"""
        try:
            # 매물 유형 선택
            if property_type == "APT":
                await page.click('button:has-text("아파트")')
            elif property_type == "OPST":
                await page.click('button:has-text("오피스텔")')
            elif property_type == "VL":
                await page.click('button:has-text("빌라")')
                
            await page.wait_for_timeout(1000)
            
            # 거래 유형 선택
            if trade_type == "A1":
                await page.click('button:has-text("매매")')
            elif trade_type == "B1":
                await page.click('button:has-text("전세")')
            elif trade_type == "B2":
                await page.click('button:has-text("월세")')
                
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            logger.warning(f"Error applying filters: {e}")
            
    async def _extract_properties(self, page) -> List[Dict]:
        """현재 페이지에서 매물 목록 추출"""
        properties = []
        
        try:
            # 매물 아이템 선택자 (실제 선택자는 페이지 구조에 따라 조정 필요)
            items = await page.query_selector_all('article.item')
            
            for item in items:
                try:
                    # 기본 정보 추출
                    property_info = {}
                    
                    # ID
                    article_id = await item.get_attribute('data-article-no')
                    if article_id:
                        property_info['id'] = article_id
                        
                    # 제목
                    title_elem = await item.query_selector('.item_title')
                    if title_elem:
                        property_info['title'] = await title_elem.inner_text()
                        
                    # 가격
                    price_elem = await item.query_selector('.price')
                    if price_elem:
                        property_info['price_str'] = await price_elem.inner_text()
                        
                    # 면적
                    area_elem = await item.query_selector('.area')
                    if area_elem:
                        property_info['area_str'] = await area_elem.inner_text()
                        
                    # 주소
                    addr_elem = await item.query_selector('.address')
                    if addr_elem:
                        property_info['address'] = await addr_elem.inner_text()
                        
                    # 설명
                    desc_elem = await item.query_selector('.item_detail')
                    if desc_elem:
                        property_info['description'] = await desc_elem.inner_text()
                        
                    properties.append(property_info)
                    
                except Exception as e:
                    logger.debug(f"Error extracting property item: {e}")
                    
        except Exception as e:
            logger.error(f"Error extracting properties: {e}")
            
        return properties
        
    async def _get_property_detail(self, page, basic_info: Dict) -> Optional[Dict]:
        """매물 상세 정보 수집"""
        # 기본 정보만 반환 (상세 페이지 접근은 선택적)
        return basic_info
        
    async def _go_to_next_page(self, page) -> bool:
        """다음 페이지로 이동"""
        try:
            # 다음 페이지 버튼 찾기
            next_button = await page.query_selector('a.btn_next:not(.disabled)')
            if next_button:
                await next_button.click()
                await page.wait_for_timeout(2000)
                return True
        except Exception as e:
            logger.debug(f"No more pages or error: {e}")
            
        return False
        
    async def parse_property(self, data: Dict) -> Dict:
        """
        네이버 부동산 데이터를 표준 형식으로 변환
        
        Args:
            data: 원본 데이터
            
        Returns:
            정규화된 매물 정보
        """
        parsed = {
            'id': self.create_property_id('naver', data.get('id', '')),
            'platform': 'naver',
            'title': data.get('title', ''),
            'price': self.normalize_price(data.get('price_str', '')),
            'area': self.normalize_area(data.get('area_str', '')),
            'address': data.get('address', ''),
            'description': data.get('description', ''),
            'floor': data.get('floor', ''),
            'url': f"{self.base_url}/article/{data.get('id', '')}",
            'collected_at': datetime.now().isoformat(),
            'raw_data': data  # 원본 데이터 보존
        }
        
        # 평수 계산
        if parsed['area']:
            parsed['pyeong'] = round(parsed['area'] / 3.3058, 1)
            
        return parsed