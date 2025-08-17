"""
강남구 삼성1동 전체 매물 수집 - 개선 버전
모든 페이지를 순회하며 실제 전체 매물 수집
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


class EnhancedNaverCollector(NaverMobileCollector):
    """개선된 네이버 부동산 크롤러 - 전체 페이지 수집"""
    
    async def search_area_full(
        self, 
        area: str,
        property_types: list,
        trade_type: TradeType,
        max_pages: int = 50  # 최대 50페이지까지 검색
    ):
        """모든 페이지의 매물을 수집"""
        
        results = {
            "area": area,
            "trade_type": trade_type.value,
            "search_time": datetime.now().isoformat(),
            "properties": []
        }
        
        for prop_type in property_types:
            print(f"    🔍 {prop_type.value} 검색 중...", end="")
            all_properties = []
            
            try:
                # 여러 페이지 순회
                for page in range(1, max_pages + 1):
                    page_props = await self._search_page(area, prop_type, trade_type, page)
                    
                    if not page_props:  # 더 이상 매물이 없으면 중단
                        break
                        
                    all_properties.extend(page_props)
                    
                    # 진행 상황 표시
                    if page % 5 == 0:
                        print(f".", end="")
                    
                    # API 제한 방지
                    await asyncio.sleep(0.3)
                    
                    # 페이지당 20개씩이므로, 마지막 페이지가 20개 미만이면 끝
                    if len(page_props) < 20:
                        break
                
                print(f" ✅ {len(all_properties)}개 발견")
                results["properties"].extend(all_properties)
                
            except Exception as e:
                print(f" ❌ 오류: {e}")
                continue
        
        return results
    
    async def _search_page(
        self,
        area: str,
        property_type: PropertyType,
        trade_type: TradeType,
        page: int
    ):
        """특정 페이지의 매물 검색"""
        
        # 삼성1동 좌표 (더 넓은 범위)
        lat, lng = 37.5088, 127.0627
        
        # 매물 유형에 따라 적절한 코드 사용
        type_codes = {
            PropertyType.APT: "APT",
            PropertyType.OFFICETEL: "OPST",
            PropertyType.VILLA: "VL",
            PropertyType.ONEROOM: "OR",
            PropertyType.RETAIL: "SMS",
            PropertyType.OFFICE: "GJCG",
            PropertyType.DETACHED: "DDDGG",
            PropertyType.TOWNHOUSE: "JWJT",
            PropertyType.RETAIL_HOUSE: "SGJT",
        }
        
        type_code = type_codes.get(property_type, "APT")
        
        # API 파라미터 - 더 넓은 범위
        params = {
            "rletTpCd": type_code,
            "tradTpCd": self._get_trade_code(trade_type),
            "z": "14",  # 줌 레벨 조정 (더 넓은 범위)
            "lat": str(lat),
            "lon": str(lng),
            "btm": str(lat - 0.015),  # 더 넓은 범위
            "lft": str(lng - 0.015),
            "top": str(lat + 0.015),
            "rgt": str(lng + 0.015),
            "cortarNo": "",
            "page": str(page)  # 페이지 번호
        }
        
        properties = []
        
        try:
            async with self.session.get(
                self.ARTICLE_API,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "body" in data and isinstance(data["body"], list):
                        for article in data["body"]:
                            property_info = self._parse_article(article, property_type)
                            if property_info:
                                properties.append(property_info)
                                
        except Exception as e:
            # 에러는 조용히 처리
            pass
            
        return properties


async def collect_samsung1dong_full():
    """삼성1동 전체 매물 수집 - 개선 버전"""
    
    # 주요 매물 유형만 선택 (시간 단축)
    selected_property_types = [
        PropertyType.APT,           # 아파트
        PropertyType.OFFICETEL,     # 오피스텔
        PropertyType.VILLA,         # 빌라
        PropertyType.ONEROOM,       # 원룸
    ]
    
    # 모든 거래 유형
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
        "properties": [],
        "duplicate_removed": 0
    }
    
    # 중복 제거를 위한 세트
    seen_ids = set()
    
    async with EnhancedNaverCollector() as collector:
        print("=" * 60)
        print("🏢 강남구 삼성1동 전체 매물 수집 - 전체 페이지 버전")
        print("=" * 60)
        print(f"수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("⚠️  전체 페이지를 수집하므로 시간이 좀 걸립니다...")
        print()
        
        # 각 거래 유형별로 수집
        for trade_type in trade_types:
            print(f"\n📍 {trade_type.value} 매물 수집 중...")
            print("-" * 40)
            
            # 수집
            results = await collector.search_area_full(
                area="삼성1동",
                property_types=selected_property_types,
                trade_type=trade_type,
                max_pages=30  # 최대 30페이지 (600개)
            )
            
            # 결과 저장 (중복 제거)
            trade_count = 0
            for prop in results['properties']:
                prop_id = prop.get('article_id')
                
                # 중복 체크
                if prop_id and prop_id not in seen_ids:
                    seen_ids.add(prop_id)
                    
                    # 네이버 링크 추가
                    prop['naver_link'] = f"https://m.land.naver.com/article/info/{prop_id}"
                    prop['trade_type'] = trade_type.value
                    
                    all_results['properties'].append(prop)
                    trade_count += 1
                    
                    # 타입별 카운트
                    prop_type_str = prop.get('type')
                    if prop_type_str not in all_results['by_type']:
                        all_results['by_type'][prop_type_str] = 0
                    all_results['by_type'][prop_type_str] += 1
                else:
                    all_results['duplicate_removed'] += 1
            
            all_results['by_trade'][trade_type.value] = trade_count
            print(f"  📊 {trade_type.value} 총 {trade_count}개 수집 완료 (중복 제거)")
        
        # 전체 카운트
        all_results['total_properties'] = len(all_results['properties'])
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 수집 결과 요약")
        print("=" * 60)
        print(f"✅ 총 매물 수: {all_results['total_properties']}개")
        print(f"🔄 중복 제거: {all_results['duplicate_removed']}개")
        
        print("\n📈 매물 유형별:")
        for prop_type, count in all_results['by_type'].items():
            print(f"  - {prop_type}: {count}개")
        
        print("\n💰 거래 유형별:")
        for trade_type, count in all_results['by_trade'].items():
            print(f"  - {trade_type}: {count}개")
        
        # 가격 분석
        sale_prices = [p['price'] for p in all_results['properties'] 
                      if p.get('price') and p.get('trade_type') == '매매']
        if sale_prices:
            print(f"\n💵 매매가 분석:")
            print(f"  - 평균: {sum(sale_prices)/len(sale_prices):,.0f}만원")
            print(f"  - 최저: {min(sale_prices):,}만원")
            print(f"  - 최고: {max(sale_prices):,}만원")
            print(f"  - 매물 수: {len(sale_prices)}개")
        
        # JSON 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"samsung1dong_full_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 데이터 저장 완료: {filename}")
        
        # HTML 리포트 생성
        create_enhanced_html_report(all_results, timestamp)
        
        return all_results


def create_enhanced_html_report(data, timestamp):
    """개선된 HTML 리포트 생성"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>강남구 삼성1동 전체 매물 리포트 - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Noto Sans KR', sans-serif; 
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1600px; 
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            margin-bottom: 10px;
            font-size: 32px;
        }}
        .alert {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
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
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
            font-size: 14px;
        }}
        .filters {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .filter-btn {{
            padding: 8px 15px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .filter-btn:hover {{
            background: #667eea;
            color: white;
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
            z-index: 10;
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
            padding: 5px 10px;
            border: 1px solid #3498db;
            border-radius: 3px;
            transition: all 0.3s;
        }}
        .link:hover {{ 
            background: #3498db;
            color: white;
        }}
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
        .trade-매매 {{ background: #e74c3c; color: white; }}
        .trade-전세 {{ background: #3498db; color: white; }}
        .trade-월세 {{ background: #f39c12; color: white; }}
        .highlight {{
            background: #fffbf0 !important;
        }}
    </style>
    <script>
        function filterTable(type, value) {{
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach(row => {{
                if (type === 'all') {{
                    row.style.display = '';
                }} else if (type === 'trade') {{
                    const trade = row.querySelector('.trade-badge').textContent;
                    row.style.display = trade === value ? '' : 'none';
                }} else if (type === 'property') {{
                    const propType = row.querySelector('.property-badge').textContent;
                    row.style.display = propType === value ? '' : 'none';
                }}
            }});
            updateCount();
        }}
        
        function updateCount() {{
            const visibleRows = document.querySelectorAll('tbody tr:not([style*="none"])');
            document.getElementById('visible-count').textContent = visibleRows.length;
        }}
        
        function sortTable(column) {{
            // 간단한 정렬 기능
            alert('정렬 기능은 추후 구현 예정입니다.');
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>🏢 강남구 삼성1동 전체 매물 리포트</h1>
        <p style="color: #666;">수집 시간: {data['collection_time']} | 전체 페이지 수집 버전</p>
        
        <div class="alert">
            ⚠️ <strong>주의:</strong> 본 데이터는 네이버 부동산에서 수집된 정보입니다. 
            실시간 정보가 아니므로 실제 매물과 차이가 있을 수 있습니다.
        </div>
        
        <div class="summary">
            <h2 style="margin-bottom: 20px;">📊 전체 요약</h2>
            <div class="stats">
                <div class="stat-card" style="background: rgba(255,255,255,0.2);">
                    <div class="stat-number">{data['total_properties']}</div>
                    <div class="stat-label">전체 매물</div>
                </div>
                <div class="stat-card" style="background: rgba(255,255,255,0.2);">
                    <div class="stat-number">{data.get('duplicate_removed', 0)}</div>
                    <div class="stat-label">중복 제거</div>
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
        
        <div class="filters">
            <button class="filter-btn" onclick="filterTable('all', '')">🔍 전체보기</button>
            <button class="filter-btn" onclick="filterTable('trade', '매매')">💰 매매만</button>
            <button class="filter-btn" onclick="filterTable('trade', '전세')">🏠 전세만</button>
            <button class="filter-btn" onclick="filterTable('trade', '월세')">📅 월세만</button>
            <button class="filter-btn" onclick="filterTable('property', '아파트')">🏢 아파트만</button>
            <button class="filter-btn" onclick="filterTable('property', '오피스텔')">🏬 오피스텔만</button>
        </div>
        
        <h2 style="margin-top: 30px;">
            📋 매물 상세 목록 
            <span style="font-size: 16px; color: #666;">
                (표시: <span id="visible-count">""" + str(data['total_properties']) + """</span>개)
            </span>
        </h2>
        <table>
            <thead>
                <tr>
                    <th width="50">번호</th>
                    <th width="80">유형</th>
                    <th width="60">거래</th>
                    <th>매물명</th>
                    <th width="100">가격</th>
                    <th width="80">면적</th>
                    <th width="60">층수</th>
                    <th width="150">주소</th>
                    <th width="80">중개사</th>
                    <th width="60">링크</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # 매물 데이터 추가
    for i, prop in enumerate(data['properties'], 1):
        price = prop.get('price', 0)
        if price > 10000:  # 1억 이상
            price_str = f"{price/10000:.1f}억"
        else:
            price_str = f"{price:,}만원"
        
        area = prop.get('area', '-')
        area_str = f"{area}㎡" if area != '-' and area else "-"
        
        prop_type = prop.get('type', '기타')
        trade_type = prop.get('trade_type', '기타')
        
        # 고가 매물 하이라이트
        highlight_class = "highlight" if price > 1000000 else ""
        
        html_content += f"""
                <tr class="{highlight_class}">
                    <td>{i}</td>
                    <td><span class="type-badge type-{prop_type} property-badge">{prop_type}</span></td>
                    <td><span class="type-badge trade-{trade_type} trade-badge">{trade_type}</span></td>
                    <td>{prop.get('title', '-')}</td>
                    <td class="price">{price_str}</td>
                    <td>{area_str}</td>
                    <td>{prop.get('floor', '-')}</td>
                    <td>{prop.get('address', '삼성1동')}</td>
                    <td style="font-size: 11px;">{prop.get('realtor', '-')[:10]}</td>
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
                <li>중복 매물은 자동으로 제거되었습니다.</li>
                <li>100억 이상 매물은 노란색으로 표시됩니다.</li>
                <li>정확한 정보는 링크를 통해 네이버 부동산에서 확인하세요.</li>
                <li>수집 시간: """ + datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분') + """</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """
    
    # HTML 파일 저장
    html_filename = f"samsung1dong_full_{timestamp}.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 개선된 HTML 리포트 생성 완료: {html_filename}")
    print(f"   💡 필터 기능과 통계가 포함된 인터랙티브 리포트입니다!")


if __name__ == "__main__":
    asyncio.run(collect_samsung1dong_full())