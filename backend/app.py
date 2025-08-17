"""
실시간 부동산 데이터 수집 API 서버
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

app = FastAPI(title="부동산 실시간 검색 API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 캐시 저장소 (메모리)
cache = {}
CACHE_DURATION = timedelta(minutes=5)  # 5분 캐시

def is_cache_valid(cache_key: str) -> bool:
    """캐시 유효성 검사"""
    if cache_key not in cache:
        return False
    
    cached_data = cache[cache_key]
    if datetime.now() - cached_data['timestamp'] > CACHE_DURATION:
        return False
    
    return True

async def search_naver_realtime(address: str) -> List[Dict]:
    """네이버 부동산 실시간 검색"""
    properties = []
    
    try:
        # 네이버 부동산 모바일 API
        url = "https://m.land.naver.com/cluster/ajax/articleList"
        
        params = {
            "rletTpCd": "APT:OPST:VL:DDDGG:OR",  # 모든 매물 타입
            "tradTpCd": "A1:B1:B2:B3",  # 모든 거래 타입
            "z": 15,
            "cortarNo": "1168010800",  # 강남구 삼성동 코드
            "page": 1
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://m.land.naver.com/'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('body', [])[:20]:  # 상위 20개만
                        property_info = {
                            'id': f"NAVER_{item.get('atclNo', '')}",
                            'platform': 'naver',
                            'title': item.get('atclNm', ''),
                            'address': f"서울 강남구 삼성동 {item.get('bildNm', '')}",
                            'price': int(item.get('prc', 0).replace(',', '') if isinstance(item.get('prc'), str) else item.get('prc', 0)),
                            'area': item.get('spc1', 0),
                            'floor': f"{item.get('flrInfo', '')}",
                            'type': item.get('rletTpNm', ''),
                            'trade_type': item.get('tradTpNm', ''),
                            'lat': item.get('lat', 0),
                            'lng': item.get('lng', 0),
                            'description': item.get('atclFetrDesc', ''),
                            'url': f"https://m.land.naver.com/article/info/{item.get('atclNo', '')}",
                            'collected_at': datetime.now().isoformat()
                        }
                        
                        # 주소 필터링
                        if address.lower() in property_info['address'].lower():
                            properties.append(property_info)
    except Exception as e:
        print(f"네이버 검색 오류: {e}")
    
    return properties

async def search_zigbang_realtime(address: str) -> List[Dict]:
    """직방 실시간 검색"""
    properties = []
    
    try:
        # 직방 API
        url = "https://apis.zigbang.com/v2/items"
        
        params = {
            'domain': 'zigbang',
            'geohash': 'wydm6',  # 삼성동 지역 해시
            'zoom': 15,
            'item_ids': '',
            'sales_type': 'deposit|jeonse|monthly',
            'deposit_gteq': 0,
            'rent_gteq': 0
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('items', [])[:20]:
                        property_info = {
                            'id': f"ZIGBANG_{item.get('item_id', '')}",
                            'platform': 'zigbang',
                            'title': item.get('title', ''),
                            'address': item.get('address', ''),
                            'price': item.get('보증금', 0) // 10000 if item.get('보증금') else 0,
                            'area': item.get('전용면적', 0),
                            'floor': item.get('floor', ''),
                            'type': item.get('building_type', ''),
                            'trade_type': item.get('sales_type', ''),
                            'monthly_rent': item.get('월세', 0),
                            'lat': item.get('lat', 0),
                            'lng': item.get('lng', 0),
                            'description': item.get('description', ''),
                            'url': f"https://zigbang.com/home/oneroom/{item.get('item_id', '')}",
                            'collected_at': datetime.now().isoformat()
                        }
                        
                        if address.lower() in property_info.get('address', '').lower():
                            properties.append(property_info)
    except Exception as e:
        print(f"직방 검색 오류: {e}")
    
    return properties

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "running",
        "message": "부동산 실시간 검색 API",
        "endpoints": [
            "/search/realtime",
            "/search/cached",
            "/health"
        ]
    }

@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/search/realtime")
async def search_realtime(
    address: str = Query(..., description="검색할 주소"),
    platforms: str = Query("all", description="플랫폼 선택 (all, naver, zigbang, dabang, kb)")
):
    """
    실시간 부동산 매물 검색
    
    - **address**: 검색할 주소 (예: "삼성동 151-7")
    - **platforms**: 검색할 플랫폼 (기본값: all)
    """
    
    # 캐시 키 생성
    cache_key = f"{address}_{platforms}"
    
    # 캐시 확인
    if is_cache_valid(cache_key):
        cached_result = cache[cache_key]
        cached_result['cached'] = True
        return cached_result['data']
    
    # 플랫폼 선택
    selected_platforms = []
    if platforms == "all":
        selected_platforms = ["naver", "zigbang", "dabang", "kb"]
    else:
        selected_platforms = platforms.split(",")
    
    # 병렬로 모든 플랫폼 검색
    tasks = []
    
    if "naver" in selected_platforms:
        tasks.append(search_naver_realtime(address))
    
    if "zigbang" in selected_platforms:
        tasks.append(search_zigbang_realtime(address))
    
    # 다방과 KB는 기존 수집기 사용
    if "dabang" in selected_platforms:
        tasks.append(search_dabang_cached(address))
    
    if "kb" in selected_platforms:
        tasks.append(search_kb_cached(address))
    
    # 모든 플랫폼 결과 수집
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 통합
    all_properties = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append(str(result))
        elif isinstance(result, list):
            all_properties.extend(result)
    
    # 통계 계산
    stats = {
        "byPlatform": {},
        "byType": {},
        "priceRange": {
            "min": None,
            "max": None,
            "avg": None
        }
    }
    
    if all_properties:
        # 플랫폼별 집계
        for prop in all_properties:
            platform = prop.get('platform', 'unknown')
            stats['byPlatform'][platform] = stats['byPlatform'].get(platform, 0) + 1
            
            prop_type = prop.get('type', 'unknown')
            stats['byType'][prop_type] = stats['byType'].get(prop_type, 0) + 1
        
        # 가격 통계
        prices = [p['price'] for p in all_properties if p.get('price', 0) > 0]
        if prices:
            stats['priceRange'] = {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices)
            }
    
    result = {
        "query": address,
        "platforms": selected_platforms,
        "totalCount": len(all_properties),
        "properties": all_properties[:100],  # 최대 100개
        "stats": stats,
        "cached": False,
        "timestamp": datetime.now().isoformat(),
        "errors": errors if errors else None
    }
    
    # 캐시 저장
    cache[cache_key] = {
        'data': result,
        'timestamp': datetime.now()
    }
    
    return result

async def search_dabang_cached(address: str) -> List[Dict]:
    """다방 캐시된 데이터 검색"""
    # 임시로 빈 리스트 반환 (실제로는 기존 수집기 사용)
    return []

async def search_kb_cached(address: str) -> List[Dict]:
    """KB 캐시된 데이터 검색"""
    # 임시로 빈 리스트 반환 (실제로는 기존 수집기 사용)
    return []

@app.get("/api/cache/clear")
async def clear_cache():
    """캐시 초기화"""
    cache.clear()
    return {"message": "캐시가 초기화되었습니다", "timestamp": datetime.now().isoformat()}

@app.get("/api/cache/status")
async def cache_status():
    """캐시 상태 확인"""
    return {
        "total_keys": len(cache),
        "keys": list(cache.keys()),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("실시간 부동산 검색 API 서버 시작...")
    print("http://localhost:8000")
    print("API 문서: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)