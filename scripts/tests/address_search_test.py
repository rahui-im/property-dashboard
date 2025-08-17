"""
주소 기반 매물 검색 시스템 테스트
"""
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

def search_by_address(address_keyword, data_file='integrated_samsung1dong_20250817_092440.json'):
    """주소로 매물 검색"""
    
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    for prop in data['properties']:
        # 주소에 키워드가 포함된 매물 찾기
        if address_keyword.lower() in prop.get('address', '').lower():
            results.append(prop)
    
    return results

def analyze_search_results(results):
    """검색 결과 분석"""
    if not results:
        print("검색 결과가 없습니다.")
        return
    
    print(f"\n=== 검색 결과: {len(results)}개 매물 ===\n")
    
    # 플랫폼별 분류
    by_platform = {}
    for r in results:
        platform = r.get('platform', 'unknown')
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(r)
    
    # 가격 분석
    prices = [r.get('price', 0) for r in results if r.get('price', 0) > 0]
    
    print("📊 가격 정보:")
    if prices:
        print(f"  - 최저가: {min(prices):,}만원")
        print(f"  - 최고가: {max(prices):,}만원")
        print(f"  - 평균가: {sum(prices)/len(prices):,.0f}만원")
    
    print("\n📍 플랫폼별 매물:")
    for platform, props in by_platform.items():
        print(f"  - {platform}: {len(props)}개")
    
    print("\n🏢 상세 매물 목록:")
    for i, r in enumerate(results[:5], 1):  # 상위 5개만 표시
        print(f"\n[{i}] {r.get('title', '제목 없음')}")
        print(f"    주소: {r.get('address', '주소 없음')}")
        print(f"    가격: {r.get('price', 0):,}만원")
        print(f"    면적: {r.get('area', 'N/A')}")
        print(f"    층수: {r.get('floor', 'N/A')}")
        print(f"    플랫폼: {r.get('platform', 'unknown')}")
        print(f"    URL: {r.get('url', 'N/A')}")
    
    if len(results) > 5:
        print(f"\n... 외 {len(results)-5}개 매물")

# 테스트 실행
if __name__ == "__main__":
    # 예시: "삼성" 키워드로 검색
    test_addresses = [
        "삼성",
        "삼성동",
        "봉은사",
        "테헤란"
    ]
    
    for addr in test_addresses:
        print(f"\n{'='*50}")
        print(f"🔍 검색어: '{addr}'")
        results = search_by_address(addr)
        analyze_search_results(results)