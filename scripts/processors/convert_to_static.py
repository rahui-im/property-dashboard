"""
JSON 데이터를 정적 JavaScript 파일로 변환
"""
import json
import os
from datetime import datetime

def convert_to_static():
    """최신 데이터를 정적 파일로 변환"""
    
    # 가장 최근 통합 데이터 찾기
    data_files = [f for f in os.listdir('.') if f.startswith('integrated_samsung1dong')]
    if not data_files:
        # 샘플 데이터 생성
        sample_data = create_sample_data()
    else:
        # 최신 파일 읽기
        latest_file = sorted(data_files)[-1]
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        sample_data = process_data(data)
    
    # public/data.js로 저장
    js_content = f"const propertyData = {json.dumps(sample_data, ensure_ascii=False, indent=2)};"
    
    with open('public/data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print("public/data.js created successfully")
    return sample_data

def process_data(data):
    """데이터 처리 및 요약"""
    
    # 상위 100개만 선택 (파일 크기 제한)
    properties = data.get('properties', [])[:100]
    
    # 통계 데이터
    stats = {
        'total': data.get('total_count', len(properties)),
        'byPlatform': data.get('platform_stats', {}),
        'byType': {},
        'byTrade': {},
        'priceRange': {
            'min': 0,
            'max': 0,
            'avg': 0
        }
    }
    
    # 매물 유형별 집계
    for prop in properties:
        prop_type = prop.get('type', '기타')
        stats['byType'][prop_type] = stats['byType'].get(prop_type, 0) + 1
        
        trade_type = prop.get('trade_type', '기타')
        stats['byTrade'][trade_type] = stats['byTrade'].get(trade_type, 0) + 1
    
    # 가격 통계
    prices = [p.get('price', 0) for p in properties if p.get('price', 0) > 0]
    if prices:
        stats['priceRange']['min'] = min(prices)
        stats['priceRange']['max'] = max(prices)
        stats['priceRange']['avg'] = sum(prices) / len(prices)
    
    return {
        'area': '강남구 삼성1동',
        'collectionTime': data.get('collection_time', datetime.now().isoformat()),
        'stats': stats,
        'properties': properties
    }

def create_sample_data():
    """샘플 데이터 생성"""
    return {
        'area': '강남구 삼성1동',
        'collectionTime': datetime.now().isoformat(),
        'stats': {
            'total': 3340,
            'byPlatform': {
                '네이버': 840,
                '직방': 500,
                '다방': 1200,
                'KB부동산': 800
            },
            'byType': {
                '아파트': 1200,
                '오피스텔': 893,
                '원룸': 635,
                '빌라': 612
            },
            'byTrade': {
                '매매': 1800,
                '전세': 1000,
                '월세': 540
            },
            'priceRange': {
                'min': 16000,
                'max': 2100000,
                'avg': 288000
            }
        },
        'properties': []
    }

if __name__ == "__main__":
    convert_to_static()