"""
Playwright 직접 스크래핑 방식
API 인터셉트 대신 화면에서 직접 데이터 추출
"""
import asyncio
import json
import sys
import io
from datetime import datetime
import time

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def collect_with_playwright():
    """Playwright로 직접 매물 수집"""
    
    print("=" * 70)
    print("🎭 Playwright 직접 스크래핑 - 삼성1동 매물")
    print("=" * 70)
    
    async with async_playwright() as p:
        # 브라우저 실행 (headless=False로 실제 창 보기)
        browser = await p.chromium.launch(
            headless=False,  # 브라우저 창 보이기
            slow_mo=500,  # 각 동작마다 0.5초 대기 (디버깅용)
        )
        
        # 모바일 컨텍스트
        context = await browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True
        )
        
        page = await context.new_page()
        
        print("🌐 네이버 부동산 접속...")
        
        # 직접 지도 URL로 이동 (삼성1동 중심)
        await page.goto("https://m.land.naver.com/map/37.5088:127.0627:16")
        await page.wait_for_load_state("networkidle")
        
        print("⏳ 페이지 로딩 대기...")
        await asyncio.sleep(5)
        
        # 스크린샷 저장 (디버깅용)
        await page.screenshot(path="naver_land_screenshot.png")
        print("📸 스크린샷 저장: naver_land_screenshot.png")
        
        properties = []
        
        try:
            # 방법 1: 클러스터 마커 클릭
            print("\n🎯 매물 클러스터 찾기...")
            
            # 지도 위의 매물 수 표시 클릭
            markers = await page.query_selector_all(".marker_complex, .complex_link, .marker")
            print(f"  발견된 마커: {len(markers)}개")
            
            for i, marker in enumerate(markers[:5]):  # 처음 5개만
                try:
                    print(f"\n  마커 {i+1} 클릭...")
                    await marker.click()
                    await asyncio.sleep(2)
                    
                    # 매물 목록이 나타나는지 확인
                    property_items = await page.query_selector_all(".item_inner, .article_item, .item")
                    print(f"    매물 {len(property_items)}개 발견")
                    
                    for item in property_items[:10]:  # 각 마커당 10개만
                        try:
                            # 매물 정보 추출
                            title = await item.query_selector(".item_title, .title, .name")
                            price = await item.query_selector(".price, .item_price")
                            area = await item.query_selector(".area, .size, .spec")
                            
                            prop_data = {
                                "title": await title.inner_text() if title else "",
                                "price": await price.inner_text() if price else "",
                                "area": await area.inner_text() if area else "",
                                "collected_at": datetime.now().isoformat()
                            }
                            
                            if prop_data["title"]:
                                properties.append(prop_data)
                                print(f"      ✅ {prop_data['title']}: {prop_data['price']}")
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"    ❌ 마커 클릭 실패: {e}")
                    continue
                    
            # 방법 2: 목록 버튼 찾기
            if len(properties) == 0:
                print("\n📋 목록 보기 시도...")
                
                list_button = await page.query_selector("button:has-text('목록'), .btn_list, [aria-label*='목록']")
                if list_button:
                    await list_button.click()
                    await asyncio.sleep(2)
                    
                    # 목록에서 매물 추출
                    items = await page.query_selector_all(".item_inner, .article_item")
                    for item in items[:50]:
                        try:
                            text = await item.inner_text()
                            if text:
                                properties.append({
                                    "raw_text": text,
                                    "collected_at": datetime.now().isoformat()
                                })
                        except:
                            continue
                            
        except Exception as e:
            print(f"❌ 수집 오류: {e}")
            
        finally:
            # 브라우저 종료
            await browser.close()
            
    # 결과 출력
    print("\n" + "=" * 70)
    print("📊 수집 결과")
    print("=" * 70)
    print(f"✅ 총 {len(properties)}개 매물 수집")
    
    if properties:
        print("\n📋 샘플 데이터:")
        for i, prop in enumerate(properties[:5], 1):
            print(f"{i}. {prop}")
            
    # 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"playwright_direct_{len(properties)}_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "area": "삼성1동",
            "total": len(properties),
            "properties": properties,
            "collected_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
        
    print(f"\n💾 저장 완료: {filename}")
    
    return properties


async def test_simple():
    """간단한 테스트"""
    
    print("🧪 Playwright 간단 테스트")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("1. 네이버 메인 접속...")
        await page.goto("https://www.naver.com")
        await asyncio.sleep(2)
        
        print("2. 부동산 클릭...")
        await page.click("text=부동산")
        await asyncio.sleep(3)
        
        print("3. 스크린샷...")
        await page.screenshot(path="test_screenshot.png")
        
        await browser.close()
        print("✅ 테스트 완료!")


if __name__ == "__main__":
    # 먼저 간단한 테스트
    print("Step 1: 간단한 테스트 실행\n")
    asyncio.run(test_simple())
    
    print("\n" + "=" * 70)
    print("\nStep 2: 실제 수집 실행\n")
    asyncio.run(collect_with_playwright())