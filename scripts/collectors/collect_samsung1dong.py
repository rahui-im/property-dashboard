"""
강남구 삼성1동 전체 매물 수집 및 저장
"""
import asyncio
import json
import sys
import io
from datetime import datetime
from pathlib import Path

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(str(Path(__file__).parent))

from src.mcp.collectors.naver_mobile_collector import (
    NaverMobileCollector,
    PropertyType,
    TradeType
)


async def collect_samsung1dong():
    """삼성1동 전체 매물 수집"""
    
    # 수집할 매물 유형 (18개 전체)
    all_property_types = [
        PropertyType.APT,           # 아파트
        PropertyType.OFFICETEL,     # 오피스텔
        PropertyType.VILLA,         # 빌라
        PropertyType.ONEROOM,       # 원룸
        PropertyType.TOWNHOUSE,     # 전원주택
        PropertyType.DETACHED,      # 단독/다가구
        PropertyType.RETAIL_HOUSE,  # 상가주택
        PropertyType.RETAIL,        # 상가
        PropertyType.OFFICE,        # 사무실
    ]
    
    # 거래 유형
    trade_types = [
        TradeType.SALE,     # 매매
        TradeType.RENT,     # 전세
        TradeType.MONTHLY,  # 월세
    ]
    
    all_results = {
        "area": "강남구 삼성1동",
        "collection_time": datetime.now().isoformat(),
        "total_properties": 0,
        "by_type": {},
        "by_trade": {},
        "properties": []
    }
    
    async with NaverMobileCollector() as collector:
        print("=" * 60)
        print("🏢 강남구 삼성1동 전체 매물 수집")
        print("=" * 60)
        print(f"수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 삼성1동 좌표 설정 (더 정확한 좌표)
        # 기존 _get_coordinates 메서드 오버라이드
        original_get_coords = collector._get_coordinates
        async def samsung1_coords(area):
            return (37.5088, 127.0627)  # 삼성1동 중심 좌표
        collector._get_coordinates = samsung1_coords
        
        # 각 거래 유형별로 수집
        for trade_type in trade_types:
            print(f"\n📍 {trade_type.value} 매물 수집 중...")
            print("-" * 40)
            
            trade_results = {
                "type": trade_type.value,
                "count": 0,
                "properties": []
            }
            
            # 각 매물 유형별로 수집
            for prop_type in all_property_types:
                try:
                    print(f"  🔍 {prop_type.value} 검색 중...", end="")
                    
                    results = await collector.search_area(
                        area="삼성1동",
                        property_types=[prop_type],
                        trade_type=trade_type
                    )
                    
                    count = len(results.get('properties', []))
                    if count > 0:
                        print(f" ✅ {count}개 발견")
                        
                        # 결과 저장
                        for prop in results['properties']:
                            # 네이버 부동산 링크 추가
                            prop['naver_link'] = f"https://m.land.naver.com/article/info/{prop.get('article_id')}"
                            prop['trade_type'] = trade_type.value
                            
                            all_results['properties'].append(prop)
                            trade_results['properties'].append(prop)
                            
                            # 타입별 카운트
                            prop_type_str = prop.get('type')
                            if prop_type_str not in all_results['by_type']:
                                all_results['by_type'][prop_type_str] = 0
                            all_results['by_type'][prop_type_str] += 1
                    else:
                        print(f" - 없음")
                    
                    # API 제한 방지
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f" ❌ 오류: {e}")
                    continue
            
            trade_results['count'] = len(trade_results['properties'])
            all_results['by_trade'][trade_type.value] = trade_results['count']
            
            print(f"\n  📊 {trade_type.value} 총 {trade_results['count']}개 수집 완료")
        
        # 전체 카운트
        all_results['total_properties'] = len(all_results['properties'])
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 수집 결과 요약")
        print("=" * 60)
        print(f"✅ 총 매물 수: {all_results['total_properties']}개")
        
        print("\n📈 매물 유형별:")
        for prop_type, count in all_results['by_type'].items():
            print(f"  - {prop_type}: {count}개")
        
        print("\n💰 거래 유형별:")
        for trade_type, count in all_results['by_trade'].items():
            print(f"  - {trade_type}: {count}개")
        
        # 가격 분석
        prices = [p['price'] for p in all_results['properties'] if p.get('price') and p.get('trade_type') == '매매']
        if prices:
            print(f"\n💵 매매가 분석:")
            print(f"  - 평균: {sum(prices)/len(prices):,.0f}만원")
            print(f"  - 최저: {min(prices):,}만원")
            print(f"  - 최고: {max(prices):,}만원")
        
        # JSON 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"samsung1dong_properties_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 데이터 저장 완료: {filename}")
        
        # HTML 리포트 생성
        create_html_report(all_results, timestamp)
        
        return all_results


def create_html_report(data, timestamp):
    """HTML 리포트 생성"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>강남구 삼성1동 매물 리포트 - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Noto Sans KR', sans-serif; 
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .summary {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .stats {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
        }}
        th {{ 
            background: #667eea; 
            color: white; 
            padding: 12px; 
            text-align: left;
            position: sticky;
            top: 0;
        }}
        td {{ 
            padding: 10px; 
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{ background: #f9f9f9; }}
        .price {{ 
            color: #e74c3c; 
            font-weight: bold;
        }}
        .link {{ 
            color: #3498db; 
            text-decoration: none;
        }}
        .link:hover {{ text-decoration: underline; }}
        .type-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .type-아파트 {{ background: #3498db; color: white; }}
        .type-오피스텔 {{ background: #9b59b6; color: white; }}
        .type-빌라 {{ background: #e67e22; color: white; }}
        .type-원룸 {{ background: #2ecc71; color: white; }}
        .type-상가 {{ background: #e74c3c; color: white; }}
        .type-사무실 {{ background: #95a5a6; color: white; }}
        .trade-매매 {{ background: #e74c3c; color: white; }}
        .trade-전세 {{ background: #3498db; color: white; }}
        .trade-월세 {{ background: #f39c12; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 강남구 삼성1동 부동산 매물 리포트</h1>
        <p style="color: #666;">수집 시간: {data['collection_time']}</p>
        
        <div class="summary">
            <h2>📊 전체 요약</h2>
            <div class="stats">
                <div class="stat-card" style="background: rgba(255,255,255,0.2);">
                    <div class="stat-number">{data['total_properties']}</div>
                    <div class="stat-label">전체 매물</div>
                </div>
    """
    
    # 거래 유형별 통계
    for trade_type, count in data['by_trade'].items():
        html_content += f"""
                <div class="stat-card" style="background: rgba(255,255,255,0.2);">
                    <div class="stat-number">{count}</div>
                    <div class="stat-label">{trade_type}</div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
        
        <h2 style="margin-top: 30px;">📋 매물 상세 목록</h2>
        <table>
            <thead>
                <tr>
                    <th>번호</th>
                    <th>유형</th>
                    <th>거래</th>
                    <th>매물명</th>
                    <th>가격</th>
                    <th>면적</th>
                    <th>층수</th>
                    <th>주소</th>
                    <th>링크</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # 매물 데이터 추가
    for i, prop in enumerate(data['properties'], 1):
        price = prop.get('price', 0)
        price_str = f"{price:,}만원" if price else "-"
        area = prop.get('area', '-')
        area_str = f"{area}㎡" if area != '-' else "-"
        
        prop_type = prop.get('type', '기타')
        trade_type = prop.get('trade_type', '기타')
        
        html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td><span class="type-badge type-{prop_type}">{prop_type}</span></td>
                    <td><span class="type-badge trade-{trade_type}">{trade_type}</span></td>
                    <td>{prop.get('title', '-')}</td>
                    <td class="price">{price_str}</td>
                    <td>{area_str}</td>
                    <td>{prop.get('floor', '-')}</td>
                    <td>{prop.get('address', '-')}</td>
                    <td><a href="{prop.get('naver_link', '#')}" target="_blank" class="link">보기</a></td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
        
        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3>📌 참고사항</h3>
            <ul style="color: #666; line-height: 1.8; padding-left: 20px;">
                <li>본 데이터는 네이버 부동산에서 수집된 정보입니다.</li>
                <li>실시간 데이터가 아니므로 실제 매물 정보와 차이가 있을 수 있습니다.</li>
                <li>정확한 정보는 링크를 통해 네이버 부동산에서 확인하세요.</li>
                <li>수집 시간: """ + datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분') + """</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """
    
    # HTML 파일 저장
    html_filename = f"samsung1dong_report_{timestamp}.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 HTML 리포트 생성 완료: {html_filename}")


if __name__ == "__main__":
    asyncio.run(collect_samsung1dong())