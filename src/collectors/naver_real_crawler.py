"""
네이버 부동산 실제 크롤러
봇 탐지 회피 및 실제 데이터 수집
"""

import asyncio
import random
import json
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
import aiohttp
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NaverRealEstateCrawler:
    """네이버 부동산 실제 크롤러"""
    
    def __init__(self):
        self.base_url = "https://land.naver.com"
        self.headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.browser = None
        self.context = None
        
    def _get_random_user_agent(self) -> str:
        """랜덤 User-Agent 반환"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)
    
    async def _init_browser(self):
        """브라우저 초기화 (봇 탐지 회피)"""
        playwright = await async_playwright().start()
        
        # 봇 탐지 회피 설정
        self.browser = await playwright.chromium.launch(
            headless=False,  # 실제 브라우저 창 표시
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        # 컨텍스트 생성
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self._get_random_user_agent(),
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        
        # 봇 탐지 우회 스크립트 추가
        await self.context.add_init_script("""
            // Chrome driver 속성 숨기기
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Chrome 속성 추가
            window.chrome = {
                runtime: {}
            };
            
            // Permissions 속성 추가
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Plugin 배열 추가
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Language 속성 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
        """)
    
    async def _random_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """랜덤 지연 (봇 방지)"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def _human_like_scroll(self, page: Page):
        """인간처럼 스크롤"""
        scroll_height = await page.evaluate('document.body.scrollHeight')
        current_position = 0
        
        while current_position < scroll_height:
            # 랜덤한 스크롤 거리
            scroll_amount = random.randint(300, 700)
            current_position += scroll_amount
            
            # 스크롤 실행
            await page.evaluate(f'window.scrollTo(0, {current_position})')
            
            # 랜덤 지연
            await self._random_delay(0.5, 1.5)
            
            # 가끔 뒤로 스크롤
            if random.random() < 0.1:
                back_amount = random.randint(50, 200)
                current_position -= back_amount
                await page.evaluate(f'window.scrollTo(0, {current_position})')
                await self._random_delay(0.3, 0.8)
    
    async def search_area(self, area_name: str) -> List[Dict[str, Any]]:
        """지역 검색 및 매물 수집"""
        if not self.browser:
            await self._init_browser()
        
        page = await self.context.new_page()
        properties = []
        
        try:
            # 메인 페이지 접속
            logger.info(f"네이버 부동산 접속 중: {area_name}")
            await page.goto(self.base_url, wait_until='networkidle')
            await self._random_delay(2, 4)
            
            # 검색창에 지역 입력
            search_input = await page.wait_for_selector('input[placeholder*="지역"]', timeout=10000)
            await search_input.click()
            await self._random_delay(0.5, 1)
            
            # 천천히 타이핑
            for char in area_name:
                await search_input.type(char)
                await self._random_delay(0.1, 0.3)
            
            await self._random_delay(1, 2)
            
            # 검색 결과 선택
            search_results = await page.wait_for_selector('.search_suggest', timeout=5000)
            if search_results:
                first_result = await page.query_selector('.search_suggest li:first-child')
                if first_result:
                    await first_result.click()
                    await self._random_delay(2, 3)
            
            # 매물 목록 페이지 대기
            await page.wait_for_selector('.item_list', timeout=10000)
            
            # 인간처럼 스크롤
            await self._human_like_scroll(page)
            
            # 매물 데이터 수집
            properties = await self._extract_properties(page)
            
            logger.info(f"{area_name}: {len(properties)}개 매물 수집 완료")
            
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")
        finally:
            await page.close()
        
        return properties
    
    async def _extract_properties(self, page: Page) -> List[Dict[str, Any]]:
        """페이지에서 매물 정보 추출"""
        properties = []
        
        # JavaScript로 데이터 추출
        items_data = await page.evaluate("""
            () => {
                const items = [];
                const elements = document.querySelectorAll('.item_list .item');
                
                elements.forEach(item => {
                    try {
                        const data = {
                            title: item.querySelector('.item_title')?.textContent?.trim() || '',
                            price: item.querySelector('.price')?.textContent?.trim() || '',
                            area: item.querySelector('.spec')?.textContent?.trim() || '',
                            floor: item.querySelector('.floor')?.textContent?.trim() || '',
                            address: item.querySelector('.address')?.textContent?.trim() || '',
                            description: item.querySelector('.item_detail')?.textContent?.trim() || '',
                            agent: item.querySelector('.agent_name')?.textContent?.trim() || '',
                            contact: item.querySelector('.agent_tel')?.textContent?.trim() || '',
                            image: item.querySelector('img')?.src || '',
                            link: item.querySelector('a')?.href || ''
                        };
                        
                        if (data.title && data.price) {
                            items.push(data);
                        }
                    } catch (e) {
                        console.error('아이템 추출 오류:', e);
                    }
                });
                
                return items;
            }
        """)
        
        # 데이터 가공
        for item in items_data:
            try:
                property_data = {
                    'id': self._generate_id(item),
                    'platform': '네이버부동산',
                    'title': item['title'],
                    'price': self._parse_price(item['price']),
                    'area': self._parse_area(item['area']),
                    'floor': item['floor'],
                    'address': item['address'],
                    'description': item['description'],
                    'agent': item['agent'],
                    'contact': item['contact'],
                    'image_url': item['image'],
                    'detail_url': item['link'],
                    'collected_at': datetime.now().isoformat()
                }
                properties.append(property_data)
            except Exception as e:
                logger.error(f"데이터 가공 중 오류: {e}")
                continue
        
        return properties
    
    def _generate_id(self, item: Dict) -> str:
        """고유 ID 생성"""
        import hashlib
        unique_string = f"{item['title']}_{item['address']}_{item['price']}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def _parse_price(self, price_str: str) -> Dict[str, Any]:
        """가격 파싱"""
        price_str = price_str.replace(',', '').replace(' ', '')
        
        result = {
            'type': '매매',
            'amount': 0,
            'deposit': 0,
            'monthly_rent': 0,
            'raw': price_str
        }
        
        try:
            if '매매' in price_str:
                result['type'] = '매매'
                # 억/만원 파싱
                if '억' in price_str:
                    parts = price_str.split('억')
                    result['amount'] = int(parts[0]) * 10000
                    if len(parts) > 1 and parts[1]:
                        extra = parts[1].replace('만원', '').replace('만', '')
                        if extra.isdigit():
                            result['amount'] += int(extra)
                elif '만' in price_str:
                    result['amount'] = int(price_str.replace('만원', '').replace('만', ''))
            
            elif '전세' in price_str:
                result['type'] = '전세'
                if '억' in price_str:
                    parts = price_str.split('억')
                    result['deposit'] = int(parts[0]) * 10000
                    if len(parts) > 1 and parts[1]:
                        extra = parts[1].replace('만원', '').replace('만', '')
                        if extra.isdigit():
                            result['deposit'] += int(extra)
            
            elif '월세' in price_str or '/' in price_str:
                result['type'] = '월세'
                parts = price_str.split('/')
                if len(parts) >= 2:
                    # 보증금
                    deposit_str = parts[0].replace('월세', '')
                    if '억' in deposit_str:
                        deposit_parts = deposit_str.split('억')
                        result['deposit'] = int(deposit_parts[0]) * 10000
                    elif deposit_str.replace('만', '').isdigit():
                        result['deposit'] = int(deposit_str.replace('만', ''))
                    
                    # 월세
                    rent_str = parts[1].replace('만', '')
                    if rent_str.isdigit():
                        result['monthly_rent'] = int(rent_str)
        except Exception as e:
            logger.error(f"가격 파싱 오류: {price_str}, {e}")
        
        return result
    
    def _parse_area(self, area_str: str) -> Dict[str, Any]:
        """면적 파싱"""
        result = {
            'supply': 0,  # 공급면적
            'exclusive': 0,  # 전용면적
            'raw': area_str
        }
        
        try:
            area_str = area_str.replace(' ', '').replace('㎡', '')
            
            if '/' in area_str:
                parts = area_str.split('/')
                if len(parts) >= 2:
                    supply = parts[0].replace('공급', '').replace('평', '')
                    exclusive = parts[1].replace('전용', '').replace('평', '')
                    
                    if supply.replace('.', '').isdigit():
                        result['supply'] = float(supply)
                    if exclusive.replace('.', '').isdigit():
                        result['exclusive'] = float(exclusive)
            else:
                # 단일 면적인 경우
                area_num = area_str.replace('평', '').replace('전용', '').replace('공급', '')
                if area_num.replace('.', '').isdigit():
                    result['exclusive'] = float(area_num)
                    result['supply'] = float(area_num)
        except Exception as e:
            logger.error(f"면적 파싱 오류: {area_str}, {e}")
        
        return result
    
    async def close(self):
        """브라우저 종료"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


# 테스트 실행
async def test_crawler():
    """크롤러 테스트"""
    crawler = NaverRealEstateCrawler()
    
    try:
        # 강남구 매물 검색
        properties = await crawler.search_area("강남구 아파트")
        
        print(f"\n=== 수집 결과 ===")
        print(f"총 {len(properties)}개 매물 수집\n")
        
        # 처음 3개만 출력
        for i, prop in enumerate(properties[:3], 1):
            print(f"\n[매물 {i}]")
            print(f"제목: {prop['title']}")
            print(f"가격: {prop['price']}")
            print(f"면적: {prop['area']}")
            print(f"주소: {prop['address']}")
            print(f"중개사: {prop['agent']}")
            print("-" * 50)
        
        # JSON 파일로 저장
        with open('naver_properties.json', 'w', encoding='utf-8') as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SUCCESS] 데이터가 naver_properties.json에 저장되었습니다.")
        
    finally:
        await crawler.close()


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(test_crawler())