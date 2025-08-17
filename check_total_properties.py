"""
삼성1동 실제 전체 매물 수 확인
"""
import asyncio
import aiohttp
import json
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def check_total_count():
    """실제 전체 매물 수 확인"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://m.land.naver.com/',
    }
    
    # 삼성1동 좌표
    lat = 37.5088
    lng = 127.0627
    
    print("=" * 60)
    print("🔍 삼성1동 실제 전체 매물 수 확인")
    print("=" * 60)
    
    # 다양한 매물 유형과 거래 유형 조합
    property_types = [
        ("APT", "아파트"),
        ("OPST", "오피스텔"),
        ("VL", "빌라"),
        ("OR", "원룸"),
        ("DDDGG", "단독/다가구"),
        ("JWJT", "전원주택"),
        ("SGJT", "상가주택"),
        ("SMS", "상가"),
        ("GJCG", "사무실/공장")
    ]
    
    trade_types = [
        ("A1", "매매"),
        ("B1", "전세"),
        ("B2", "월세")
    ]
    
    total_count = 0
    detail_counts = {}
    
    async with aiohttp.ClientSession() as session:
        for prop_code, prop_name in property_types:
            for trade_code, trade_name in trade_types:
                
                # 더 넓은 범위로 검색
                params = {
                    "rletTpCd": prop_code,
                    "tradTpCd": trade_code,
                    "z": "15",  # 더 자세한 줌 레벨
                    "lat": str(lat),
                    "lon": str(lng),
                    "btm": str(lat - 0.02),  # 더 넓은 범위
                    "lft": str(lng - 0.02),
                    "top": str(lat + 0.02),
                    "rgt": str(lng + 0.02),
                    "cortarNo": "",
                    "page": "1"
                }
                
                try:
                    # 첫 페이지 요청으로 전체 카운트 확인
                    url = "https://m.land.naver.com/cluster/ajax/articleList"
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # more 필드로 추가 페이지 확인
                            has_more = data.get("more", False)
                            items = data.get("body", [])
                            
                            # 여러 페이지가 있으면 전체 카운트 추정
                            if has_more:
                                # 최대 페이지 확인
                                for page in range(2, 101):  # 최대 100페이지까지 확인
                                    params["page"] = str(page)
                                    async with session.get(url, params=params, headers=headers) as resp:
                                        if resp.status == 200:
                                            page_data = await resp.json()
                                            items_count = len(page_data.get("body", []))
                                            if items_count == 0:
                                                break
                                            if not page_data.get("more", False) and items_count < 20:
                                                # 마지막 페이지
                                                estimated = (page - 1) * 20 + items_count
                                                break
                                        await asyncio.sleep(0.2)  # Rate limiting
                                else:
                                    estimated = 2000  # 100페이지 이상
                            else:
                                estimated = len(items)
                            
                            if estimated > 0:
                                key = f"{prop_name}_{trade_name}"
                                detail_counts[key] = estimated
                                total_count += estimated
                                print(f"✅ {prop_name} {trade_name}: {estimated:,}개")
                            
                except Exception as e:
                    print(f"❌ {prop_name} {trade_name} 확인 실패: {e}")
                
                await asyncio.sleep(0.5)  # API 제한 방지
    
    print("\n" + "=" * 60)
    print("📊 집계 결과")
    print("=" * 60)
    
    # 거래 유형별 합계
    for trade_code, trade_name in trade_types:
        trade_sum = sum(v for k, v in detail_counts.items() if trade_name in k)
        if trade_sum > 0:
            print(f"📍 {trade_name} 총합: {trade_sum:,}개")
    
    # 매물 유형별 합계
    print("\n📈 매물 유형별:")
    for prop_code, prop_name in property_types:
        prop_sum = sum(v for k, v in detail_counts.items() if prop_name in k)
        if prop_sum > 0:
            print(f"  - {prop_name}: {prop_sum:,}개")
    
    print(f"\n🎯 전체 매물 수: {total_count:,}개")
    
    return total_count, detail_counts


async def main():
    total, details = await check_total_count()
    
    if total > 1000:
        print("\n" + "⚠️ " * 20)
        print("실제로 수천 개의 매물이 있습니다!")
        print("전체 수집을 원하시면 시간이 오래 걸릴 수 있습니다.")
        print("⚠️ " * 20)


if __name__ == "__main__":
    asyncio.run(main())