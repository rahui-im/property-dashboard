"""
네이버 부동산 실시간 검색 - 좌표 기반 접근
"""

import requests
import json
import sys
import io
from datetime import datetime

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def search_by_coordinates():
    """좌표 기반으로 네이버 부동산 매물 검색"""
    
    print("\n🏢 네이버 부동산 - 삼성동 지역 매물 검색")
    print("="*60)
    
    # 삼성동 중심 좌표
    lat = 37.5172  # 위도
    lng = 127.0473  # 경도
    
    # 지도 범위 계산 (삼성동 주변)
    btm = lat - 0.01  # 하단 위도
    top = lat + 0.01  # 상단 위도
    lft = lng - 0.01  # 좌측 경도
    rgt = lng + 0.01  # 우측 경도
    
    print(f"📍 검색 범위: 위도 {btm:.4f}~{top:.4f}, 경도 {lft:.4f}~{rgt:.4f}")
    
    # API URL
    url = "https://m.land.naver.com/cluster/ajax/articleList"
    
    # 파라미터 설정
    params = {
        "rletTpCd": "APT:OPST",  # 아파트, 오피스텔
        "tradTpCd": "A1:B1:B2",  # 매매, 전세, 월세
        "z": 16,  # 줌 레벨 (더 상세하게)
        "lat": lat,
        "lon": lng,
        "btm": btm,
        "lft": lft,
        "top": top,
        "rgt": rgt,
        "page": 1,
        "articleOrder": "A02",
        "realEstateType": "APT:OPST",
        "tradeType": "",
        "tag": ":::::::::",
        "rentPriceMin": 0,
        "rentPriceMax": 900000000,
        "priceMin": 0,
        "priceMax": 900000000,
        "areaMin": 0,
        "areaMax": 900,
        "cortarNo": "",
        "showR0": "true"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.land.naver.com/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 매물 목록 추출
            articles = data.get('body', [])
            
            if articles:
                print(f"\n✅ 총 {len(articles)}개 매물 발견!")
                print("-"*60)
                
                # 상위 10개 매물 표시
                for idx, item in enumerate(articles[:10], 1):
                    print(f"\n🏠 매물 {idx}")
                    print(f"  📌 이름: {item.get('atclNm', 'N/A')}")
                    print(f"  🏢 건물: {item.get('bildNm', 'N/A')}")
                    print(f"  💰 가격: {item.get('prc', 'N/A')}만원")
                    print(f"  📐 면적: {item.get('spc1', 'N/A')}m² ({item.get('spc2', 'N/A')}평)")
                    print(f"  🏗️ 층: {item.get('flrInfo', 'N/A')}")
                    print(f"  📅 확인: {item.get('cfmYmd', 'N/A')}")
                    print(f"  🔗 링크: https://m.land.naver.com/article/info/{item.get('atclNo', '')}")
                
                return articles
            else:
                print("⚠️ 매물이 없습니다.")
                print(f"응답: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return []

def search_with_keyword(keyword="삼성동"):
    """키워드로 지역 검색 후 매물 조회"""
    
    print(f"\n🔍 키워드 검색: {keyword}")
    print("-"*40)
    
    # 1단계: 지역 검색
    search_url = "https://land.naver.com/search/search.naver"
    params = {
        "query": keyword
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(search_url, params=params, headers=headers)
        if response.status_code == 200:
            print(f"✅ 지역 검색 성공")
            # 실제로는 여기서 지역 코드를 파싱해야 함
        else:
            print(f"❌ 지역 검색 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    # 좌표 기반 검색
    properties = search_by_coordinates()
    
    # 키워드 검색도 시도
    # search_with_keyword("삼성동 151-7")