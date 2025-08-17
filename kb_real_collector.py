#!/usr/bin/env python3
"""
KB부동산 웹 스크래핑을 통한 삼성1동 매물 수집기
Playwright를 사용하여 실제 웹사이트를 스크래핑합니다.
"""

import asyncio
import json
from datetime import datetime
from loguru import logger
import sys
from playwright.async_api import async_playwright

# 한글 출력 설정
sys.stdout.reconfigure(encoding='utf-8')


class KBRealCollector:
    """KB부동산 웹 스크래핑 수집기"""
    
    def __init__(self):
        self.base_url = "https://onland.kbstar.com"
        self.search_url = "https://onland.kbstar.com/quics?page=C020800&cc=b061373:b061374"
        
    async def collect_samsung1dong(self, max_items=2000):
        """삼성1동 매물 수집"""
        properties = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # 1. 아파트 매물 수집
                apt_properties = await self._collect_apartments(page, max_items // 2)
                properties.extend(apt_properties)
                
                # 2. 다양한 조건으로 검색
                search_properties = await self._collect_by_search(page, max_items // 2)
                properties.extend(search_properties)
                
            except Exception as e:
                logger.error(f"Browser error: {e}")
                
            finally:
                await browser.close()
        
        # 중복 제거
        unique_properties = self._remove_duplicates(properties)
        
        logger.info(f"Total collected: {len(unique_properties)} properties from KB")
        return unique_properties
    
    async def _collect_apartments(self, page, max_items):
        """아파트 매물 수집"""
        properties = []
        
        try:
            # KB부동산 아파트 검색 페이지로 이동
            await page.goto(self.search_url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 지역 검색 - 강남구 삼성1동
            try:
                # 지역 검색 입력
                search_input = page.locator('input[placeholder*="검색"], input[name*="search"], #searchInput')
                if await search_input.count() > 0:
                    await search_input.first.fill('강남구 삼성1동')
                    await page.wait_for_timeout(1000)
                    await search_input.first.press('Enter')
                    await page.wait_for_timeout(3000)
                    
            except Exception as e:
                logger.warning(f"Search input error: {e}")
            
            # 매물 유형 선택 (아파트)
            try:
                apt_checkbox = page.locator('input[type="checkbox"][value*="아파트"], label:has-text("아파트")')
                if await apt_checkbox.count() > 0:
                    await apt_checkbox.first.check()
                    await page.wait_for_timeout(2000)
                    
            except Exception as e:
                logger.warning(f"Apartment checkbox error: {e}")
            
            # 매매 선택
            try:
                sales_checkbox = page.locator('input[type="checkbox"][value*="매매"], label:has-text("매매")')
                if await sales_checkbox.count() > 0:
                    await sales_checkbox.first.check()
                    await page.wait_for_timeout(2000)
                    
            except Exception as e:
                logger.warning(f"Sales checkbox error: {e}")
            
            # 검색 버튼 클릭
            try:
                search_btn = page.locator('button:has-text("검색"), input[type="submit"], .search-btn')
                if await search_btn.count() > 0:
                    await search_btn.first.click()
                    await page.wait_for_timeout(5000)
                    
            except Exception as e:
                logger.warning(f"Search button error: {e}")
            
            # 매물 목록 추출
            properties = await self._extract_property_list(page, max_items)
            
        except Exception as e:
            logger.error(f"Error collecting apartments: {e}")
            
        return properties
    
    async def _collect_by_search(self, page, max_items):
        """다양한 검색 조건으로 매물 수집"""
        properties = []
        
        search_terms = [
            '서울 강남구 삼성1동',
            '강남구 삼성동',
            '삼성1동 아파트',
            '삼성1동 오피스텔'
        ]
        
        for term in search_terms:
            try:
                logger.info(f"Searching for: {term}")
                
                # 새로운 검색
                await page.goto(self.search_url, wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # 검색어 입력
                search_input = page.locator('input[placeholder*="검색"], input[name*="search"], #searchInput')
                if await search_input.count() > 0:
                    await search_input.first.fill(term)
                    await page.wait_for_timeout(1000)
                    await search_input.first.press('Enter')
                    await page.wait_for_timeout(5000)
                
                # 매물 목록 추출
                term_properties = await self._extract_property_list(page, max_items // len(search_terms))
                properties.extend(term_properties)
                
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                logger.error(f"Error searching for '{term}': {e}")
                
        return properties
    
    async def _extract_property_list(self, page, max_items):
        """페이지에서 매물 목록 추출"""
        properties = []
        
        try:
            # 매물 리스트 셀렉터들
            property_selectors = [
                '.property-item',
                '.list-item',
                '.property-list-item',
                '.real-estate-item',
                'tr[class*="item"]',
                '.item-row'
            ]
            
            items = None
            for selector in property_selectors:
                items = page.locator(selector)
                count = await items.count()
                if count > 0:
                    logger.info(f"Found {count} items with selector: {selector}")
                    break
            
            if not items or await items.count() == 0:
                # 테이블 형태의 매물 목록 찾기
                table_rows = page.locator('table tbody tr, .table tbody tr')
                if await table_rows.count() > 0:
                    items = table_rows
                    logger.info(f"Found {await items.count()} table rows")
                else:
                    logger.warning("No property items found")
                    return properties
            
            # 각 매물 정보 추출
            count = min(await items.count(), max_items)
            
            for i in range(count):
                try:
                    item = items.nth(i)
                    prop_data = await self._extract_property_data(item)
                    
                    if prop_data and self._is_in_samsung1dong(prop_data):
                        properties.append(prop_data)
                        
                    if len(properties) >= max_items:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error extracting property {i}: {e}")
                    
            # 다음 페이지 확인 및 처리
            if len(properties) < max_items:
                try:
                    next_btn = page.locator('a:has-text("다음"), button:has-text("다음"), .next, .pagination .next')
                    if await next_btn.count() > 0 and await next_btn.first.is_enabled():
                        await next_btn.first.click()
                        await page.wait_for_timeout(3000)
                        
                        # 재귀적으로 다음 페이지 처리
                        next_properties = await self._extract_property_list(page, max_items - len(properties))
                        properties.extend(next_properties)
                        
                except Exception as e:
                    logger.debug(f"Next page error: {e}")
                    
        except Exception as e:
            logger.error(f"Error extracting property list: {e}")
            
        return properties
    
    async def _extract_property_data(self, item):
        """개별 매물 데이터 추출"""
        try:
            # 텍스트 추출 헬퍼 함수
            async def get_text(selector):
                try:
                    element = item.locator(selector)
                    if await element.count() > 0:
                        text = await element.first.text_content()
                        return text.strip() if text else ""
                    return ""
                except:
                    return ""
            
            # 기본 정보 추출
            title = await get_text('.title, .property-title, .name, td:nth-child(1), td:nth-child(2)')
            address = await get_text('.address, .location, .addr, td:nth-child(3), td:nth-child(4)')
            price_text = await get_text('.price, .amount, td:nth-child(5), td:nth-child(6)')
            area_text = await get_text('.area, .size, td:nth-child(7), td:nth-child(8)')
            floor_text = await get_text('.floor, td:nth-child(9), td:nth-child(10)')
            
            # 링크 추출
            link_element = item.locator('a')
            url = ""
            if await link_element.count() > 0:
                href = await link_element.first.get_attribute('href')
                if href:
                    url = href if href.startswith('http') else f"{self.base_url}{href}"
            
            # 가격 파싱
            price = self._parse_price(price_text)
            
            # 면적 파싱
            area = self._parse_area(area_text)
            
            # 고유 ID 생성
            property_id = f"KB_{hash(f'{title}{address}{price}') % 1000000}"
            
            return {
                'id': property_id,
                'platform': 'kb',
                'type': self._determine_property_type(title, address),
                'title': title,
                'address': address,
                'price': price,
                'area': area,
                'floor': floor_text,
                'description': '',
                'collected_at': datetime.now().isoformat(),
                'url': url,
                'raw_data': {
                    'title': title,
                    'address': address,
                    'price_text': price_text,
                    'area_text': area_text,
                    'floor_text': floor_text
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            return None
    
    def _parse_price(self, price_text):
        """가격 문자열 파싱"""
        try:
            if not price_text:
                return 0
                
            # 숫자와 단위 추출
            price_text = price_text.replace(',', '').replace(' ', '')
            
            # 억 단위 처리
            if '억' in price_text:
                parts = price_text.split('억')
                eok = int(''.join(filter(str.isdigit, parts[0]))) * 10000
                
                man = 0
                if len(parts) > 1 and parts[1]:
                    man_part = ''.join(filter(str.isdigit, parts[1]))
                    if man_part:
                        man = int(man_part)
                        
                return eok + man
                
            # 만원 단위
            elif '만' in price_text:
                return int(''.join(filter(str.isdigit, price_text)))
                
            # 숫자만
            else:
                numbers = ''.join(filter(str.isdigit, price_text))
                return int(numbers) if numbers else 0
                
        except Exception as e:
            logger.debug(f"Price parsing error: {price_text} - {e}")
            return 0
    
    def _parse_area(self, area_text):
        """면적 문자열 파싱"""
        try:
            if not area_text:
                return 0
                
            # 제곱미터 추출
            if '㎡' in area_text or 'm²' in area_text:
                numbers = ''.join(filter(lambda x: x.isdigit() or x == '.', area_text))
                return float(numbers) if numbers else 0
                
            # 평 단위 (평 -> 제곱미터 변환)
            elif '평' in area_text:
                numbers = ''.join(filter(lambda x: x.isdigit() or x == '.', area_text))
                pyeong = float(numbers) if numbers else 0
                return pyeong * 3.3058
                
            # 숫자만
            else:
                numbers = ''.join(filter(lambda x: x.isdigit() or x == '.', area_text))
                return float(numbers) if numbers else 0
                
        except Exception as e:
            logger.debug(f"Area parsing error: {area_text} - {e}")
            return 0
    
    def _determine_property_type(self, title, address):
        """매물 유형 결정"""
        text = f"{title} {address}".lower()
        
        if '아파트' in text:
            return '아파트'
        elif '오피스텔' in text:
            return '오피스텔'
        elif '빌라' in text or '다세대' in text:
            return '빌라'
        elif '원룸' in text or '투룸' in text:
            return '원룸'
        elif '상가' in text:
            return '상가'
        else:
            return '기타'
    
    def _is_in_samsung1dong(self, prop):
        """삼성1동 지역 내 매물인지 확인"""
        try:
            address = prop.get('address', '')
            title = prop.get('title', '')
            
            # 주소나 제목에 삼성1동 관련 키워드가 있는지 확인
            keywords = ['삼성1동', '삼성동', '강남구']
            text = f"{address} {title}".lower()
            
            return any(keyword in text for keyword in keywords)
            
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
    logger.info("🏠 KB부동산 웹 스크래핑 삼성1동 매물 수집 시작")
    
    collector = KBRealCollector()
    
    # 매물 수집
    properties = await collector.collect_samsung1dong(max_items=2000)
    
    # 결과 저장
    if properties:
        result = {
            'area': '강남구 삼성1동',
            'platform': 'kb',
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
        filename = f'kb_samsung1dong_{timestamp}.json'
        
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