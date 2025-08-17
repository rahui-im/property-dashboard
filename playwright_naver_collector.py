"""
Playwright를 사용한 네이버 부동산 실제 브라우저 크롤러
8000개 이상 매물 수집 가능
"""
import asyncio
import json
import sys
import io
from datetime import datetime
from typing import List, Dict, Any
import time

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.async_api import async_playwright, Page, Browser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightNaverCollector:
    """Playwright 기반 네이버 부동산 크롤러"""
    
    def __init__(self, headless: bool = True):
        """
        Args:
            headless: True면 브라우저 창 안보임, False면 보임
        """
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.all_properties = []
        self.seen_ids = set()
        
    async def start(self):
        """브라우저 시작"""
        self.playwright = await async_playwright().start()
        
        # 브라우저 실행 (headless=False로 하면 실제 브라우저 창이 보임)
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=CrossSiteDocumentBlockingIfIsolating',
                '--disable-site-isolation-trials'
            ]
        )
        
        # 새 페이지 생성
        context = await self.browser.new_context(
            viewport={'width': 390, 'height': 844},  # iPhone 12 Pro 크기
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True
        )
        
        self.page = await context.new_page()
        
        # 네트워크 요청 인터셉트 (API 응답 캡처)
        self.page.on("response", self._handle_response)
        
        logger.info("✅ 브라우저 시작 완료")
        
    async def _handle_response(self, response):
        """API 응답 인터셉트"""
        url = response.url
        
        # 매물 리스트 API 응답 캡처
        if "articleList" in url or "complexList" in url:
            try:
                data = await response.json()
                if "body" in data:
                    items = data.get("body", [])
                    for item in items:
                        prop_id = str(item.get("atclNo", ""))
                        if prop_id and prop_id not in self.seen_ids:
                            self.seen_ids.add(prop_id)
                            self.all_properties.append(self._parse_property(item))
                    logger.info(f"  📦 API에서 {len(items)}개 매물 캡처 (총 {len(self.all_properties)}개)")
            except:
                pass
                
    def _parse_property(self, item: Dict) -> Dict:
        """매물 정보 파싱"""
        price = item.get("prc", "0")
        if isinstance(price, str):
            price = int(price.replace(",", "")) if price and price != "-" else 0
            
        area = item.get("spc1", item.get("spc", "0"))
        if isinstance(area, str):
            try:
                area = float(area) if area and area != "-" else 0
            except:
                area = 0
                
        return {
            "article_id": str(item.get("atclNo", "")),
            "title": item.get("atclNm", ""),
            "price": price,
            "area": area,
            "floor": item.get("flrInfo", ""),
            "address": item.get("cortarNm", ""),
            "realtor": item.get("rltrNm", ""),
            "lat": item.get("lat", 0),
            "lon": item.get("lng", 0),
            "type": item.get("rletTpNm", ""),
            "trade_type": item.get("tradTpNm", ""),
            "naver_link": f"https://m.land.naver.com/article/info/{item.get('atclNo')}",
            "collected_at": datetime.now().isoformat()
        }
        
    async def collect_samsung1dong(self) -> Dict[str, Any]:
        """삼성1동 전체 매물 수집"""
        
        print("=" * 70)
        print("🎭 Playwright 브라우저 자동화 - 삼성1동 전체 매물 수집")
        print("=" * 70)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"브라우저 모드: {'Headless' if self.headless else 'Visible'}")
        print()
        
        # 네이버 부동산 모바일 접속 (더 간단한 URL)
        url = "https://m.land.naver.com"
        
        print("🌐 네이버 부동산 접속 중...")
        await self.page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # 검색창 찾기
        try:
            # 검색 버튼 클릭
            search_btn = await self.page.query_selector("button.btn_search, .search_button, [aria-label*='검색']")
            if search_btn:
                await search_btn.click()
                await asyncio.sleep(1)
            
            # 검색어 입력
            search_input = await self.page.query_selector("input[type='search'], input[placeholder*='검색'], .search_input")
            if search_input:
                await search_input.fill("강남구 삼성1동")
                await search_input.press("Enter")
                await asyncio.sleep(3)
            else:
                # 직접 URL로 이동
                map_url = "https://m.land.naver.com/map/37.5088:127.0627:15"
                await self.page.goto(map_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
        except Exception as e:
            print(f"⚠️ 검색 실패, 직접 URL 이동: {e}")
            map_url = "https://m.land.naver.com/map/37.5088:127.0627:15"
            await self.page.goto(map_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
        print("✅ 네이버 부동산 접속 완료")
        
        # 필터 설정
        await self._set_filters()
        
        # 매물 수집
        await self._collect_properties()
        
        # 결과 정리
        result = {
            "area": "강남구 삼성1동",
            "collection_time": datetime.now().isoformat(),
            "total_properties": len(self.all_properties),
            "properties": self.all_properties
        }
        
        return result
        
    async def _set_filters(self):
        """필터 설정"""
        print("\n📋 필터 설정 중...")
        
        try:
            # 필터 버튼 클릭
            filter_btn = await self.page.wait_for_selector(".filter_btn_wrap", timeout=5000)
            if filter_btn:
                await filter_btn.click()
                await asyncio.sleep(1)
                
                # 모든 매물 유형 선택
                checkboxes = await self.page.query_selector_all(".filter_item input[type='checkbox']")
                for checkbox in checkboxes:
                    is_checked = await checkbox.is_checked()
                    if not is_checked:
                        await checkbox.click()
                        await asyncio.sleep(0.1)
                
                # 적용 버튼
                apply_btn = await self.page.query_selector(".btn_apply")
                if apply_btn:
                    await apply_btn.click()
                    await asyncio.sleep(2)
                    
                print("✅ 필터 설정 완료")
        except:
            print("⚠️ 필터 설정 스킵 (기본값 사용)")
            
    async def _collect_properties(self):
        """매물 수집"""
        print("\n🔍 매물 수집 시작...")
        
        # 스크롤과 클릭으로 더 많은 매물 로드
        for attempt in range(10):  # 10번 시도
            print(f"\n📜 스크롤 {attempt + 1}/10...")
            
            # 지도 영역 이동 (더 많은 매물 로드)
            await self._move_map()
            
            # 매물 목록 열기
            await self._open_property_list()
            
            # 스크롤로 더 많은 매물 로드
            await self._scroll_property_list()
            
            print(f"  현재까지 수집: {len(self.all_properties)}개")
            
            # 8000개 이상 수집되면 종료
            if len(self.all_properties) >= 8000:
                print(f"\n🎯 목표 달성! {len(self.all_properties)}개 수집 완료")
                break
                
            await asyncio.sleep(2)
            
    async def _move_map(self):
        """지도 이동으로 더 많은 매물 로드"""
        try:
            map_element = await self.page.query_selector(".map_wrap")
            if map_element:
                # 여러 방향으로 드래그
                directions = [
                    (100, 0),    # 오른쪽
                    (-100, 0),   # 왼쪽
                    (0, 100),    # 아래
                    (0, -100),   # 위
                ]
                
                for dx, dy in directions:
                    await self.page.mouse.move(200, 400)
                    await self.page.mouse.down()
                    await self.page.mouse.move(200 + dx, 400 + dy)
                    await self.page.mouse.up()
                    await asyncio.sleep(1)
        except:
            pass
            
    async def _open_property_list(self):
        """매물 목록 열기"""
        try:
            # 매물 수 표시 클릭
            count_element = await self.page.query_selector(".complex_link")
            if not count_element:
                count_element = await self.page.query_selector(".marker_complex")
            
            if count_element:
                await count_element.click()
                await asyncio.sleep(1)
                
            # 목록 보기 버튼
            list_btn = await self.page.query_selector(".btn_list")
            if list_btn:
                await list_btn.click()
                await asyncio.sleep(1)
        except:
            pass
            
    async def _scroll_property_list(self):
        """매물 목록 스크롤"""
        try:
            # 매물 목록 컨테이너
            list_container = await self.page.query_selector(".item_list_wrap")
            if not list_container:
                list_container = await self.page.query_selector(".scroll_wrap")
                
            if list_container:
                # 여러 번 스크롤
                for _ in range(5):
                    await self.page.evaluate("""
                        const element = document.querySelector('.item_list_wrap, .scroll_wrap');
                        if (element) {
                            element.scrollTop = element.scrollHeight;
                        }
                    """)
                    await asyncio.sleep(1)
                    
                    # "더보기" 버튼이 있으면 클릭
                    more_btn = await self.page.query_selector(".btn_more")
                    if more_btn:
                        await more_btn.click()
                        await asyncio.sleep(1)
        except:
            pass
            
    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("브라우저 종료")


async def main():
    """메인 실행 함수"""
    
    # headless=False로 설정하면 실제 브라우저가 보입니다
    collector = PlaywrightNaverCollector(headless=False)  # 브라우저 보이게
    
    try:
        # 브라우저 시작
        await collector.start()
        
        # 매물 수집
        result = await collector.collect_samsung1dong()
        
        # 결과 출력
        print("\n" + "=" * 70)
        print("📊 수집 결과")
        print("=" * 70)
        print(f"✅ 총 매물 수: {result['total_properties']:,}개")
        
        # 매물 유형별 집계
        type_counts = {}
        for prop in result['properties']:
            prop_type = prop.get('type', '기타')
            type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
            
        print("\n📈 매물 유형별:")
        for prop_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {prop_type}: {count}개")
            
        # JSON 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"samsung1dong_playwright_{result['total_properties']}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 데이터 저장: {filename}")
        
        # HTML 리포트 생성
        create_html_report(result, timestamp)
        
    finally:
        # 브라우저 종료
        await collector.close()


def create_html_report(data, timestamp):
    """HTML 리포트 생성"""
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>삼성1동 Playwright 수집 - {data['total_properties']}개</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 1600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        h1 {{ margin: 0 0 10px 0; }}
        .method {{ background: #2ecc71; color: white; padding: 5px 10px; border-radius: 5px; display: inline-block; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 36px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .price {{ color: #e74c3c; font-weight: bold; }}
        .link {{ color: #3498db; text-decoration: none; padding: 5px 10px; border: 1px solid #3498db; border-radius: 3px; }}
        .link:hover {{ background: #3498db; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Playwright 브라우저 자동화 수집 결과</h1>
            <div class="method">실제 브라우저 사용</div>
            <p style="margin-top: 15px;">강남구 삼성1동 - {data['total_properties']:,}개 매물</p>
            <p>수집 시간: {data['collection_time']}</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{data['total_properties']:,}</div>
                <div class="stat-label">전체 매물</div>
            </div>
        </div>
        
        <h2>📋 매물 목록</h2>
        <table>
            <thead>
                <tr>
                    <th>번호</th>
                    <th>매물명</th>
                    <th>가격</th>
                    <th>면적</th>
                    <th>층</th>
                    <th>중개사</th>
                    <th>링크</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for i, prop in enumerate(data['properties'][:500], 1):  # 상위 500개만
        price = prop.get('price', 0)
        if price > 10000:
            price_str = f"{price/10000:.1f}억"
        else:
            price_str = f"{price:,}만원" if price else "-"
            
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{prop.get('title', '-')}</td>
                <td class="price">{price_str}</td>
                <td>{prop.get('area', '-')}㎡</td>
                <td>{prop.get('floor', '-')}</td>
                <td>{prop.get('realtor', '-')[:15]}</td>
                <td><a href="{prop.get('naver_link', '#')}" target="_blank" class="link">보기</a></td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3>🎭 Playwright 장점</h3>
            <ul>
                <li>실제 브라우저 사용으로 봇 감지 우회</li>
                <li>JavaScript 렌더링 완벽 지원</li>
                <li>네트워크 요청 인터셉트로 API 데이터 직접 캡처</li>
                <li>8000개 이상 대량 수집 가능</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """
    
    filename = f"samsung1dong_playwright_{data['total_properties']}_{timestamp}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"📄 HTML 리포트: {filename}")


if __name__ == "__main__":
    asyncio.run(main())