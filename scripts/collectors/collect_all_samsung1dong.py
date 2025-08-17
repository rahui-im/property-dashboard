"""
삼성1동 전체 8000개+ 매물 수집 - 완전판
모든 매물 유형, 모든 거래 유형, 모든 페이지
"""
import asyncio
import json
import sys
import io
from datetime import datetime
from pathlib import Path
import time

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(str(Path(__file__).parent))

from src.mcp.collectors.naver_mobile_collector import NaverMobileCollector
import aiohttp


class MaxNaverCollector(NaverMobileCollector):
    """최대 수집을 위한 개선된 크롤러"""
    
    async def collect_all_properties(self, area_name="삼성1동"):
        """모든 매물 수집"""
        
        # 삼성1동 좌표
        lat, lng = 37.5088, 127.0627
        
        # 모든 매물 유형 코드 (네이버 부동산 실제 코드)
        all_property_codes = [
            ("APT", "아파트"),
            ("OPST", "오피스텔"), 
            ("VL", "빌라"),
            ("OR", "원룸"),
            ("ABYG", "아파트분양권"),
            ("OBYG", "오피스텔분양권"),
            ("JGC", "재건축"),
            ("JWJT", "전원주택"),
            ("DDDGG", "단독/다가구"),
            ("SGJT", "상가주택"),
            ("HOJT", "한옥주택"),
            ("JGB", "재개발"),
            ("OR", "원룸"),
            ("SG", "상가"),
            ("SMS", "사무실"),
            ("GJCG", "공장/창고"),
            ("GM", "토지"),
            ("TJ", "지식산업센터")
        ]
        
        # 모든 거래 유형
        all_trade_codes = [
            ("A1", "매매"),
            ("B1", "전세"),
            ("B2", "월세"),
            ("B3", "단기임대")
        ]
        
        all_properties = []
        seen_ids = set()
        stats = {
            "by_type": {},
            "by_trade": {},
            "total": 0,
            "duplicates": 0
        }
        
        print("=" * 70)
        print("🏢 삼성1동 전체 매물 수집 - 8000개+ 목표")
        print("=" * 70)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("수집 중... (시간이 오래 걸립니다)\n")
        
        total_combinations = len(all_property_codes) * len(all_trade_codes)
        current_combo = 0
        
        for prop_code, prop_name in all_property_codes:
            for trade_code, trade_name in all_trade_codes:
                current_combo += 1
                progress = (current_combo / total_combinations) * 100
                
                print(f"\n[{progress:.1f}%] 🔍 {prop_name} - {trade_name} 수집 중...")
                combo_count = 0
                
                # 페이지별 수집 (최대 100페이지)
                for page in range(1, 101):
                    params = {
                        "rletTpCd": prop_code,
                        "tradTpCd": trade_code,
                        "z": "16",  # 최대 줌 레벨
                        "lat": str(lat),
                        "lon": str(lng),
                        "btm": str(lat - 0.025),  # 넓은 범위
                        "lft": str(lng - 0.025),
                        "top": str(lat + 0.025),
                        "rgt": str(lng + 0.025),
                        "cortarNo": "",
                        "page": str(page)
                    }
                    
                    try:
                        async with self.session.get(
                            self.ARTICLE_API,
                            params=params
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                items = data.get("body", [])
                                
                                if not items:
                                    break
                                
                                for item in items:
                                    prop_id = str(item.get("atclNo", ""))
                                    
                                    # 중복 체크
                                    if prop_id and prop_id not in seen_ids:
                                        seen_ids.add(prop_id)
                                        
                                        # 파싱
                                        property_info = self._parse_article_enhanced(
                                            item, prop_name, trade_name
                                        )
                                        
                                        if property_info:
                                            all_properties.append(property_info)
                                            combo_count += 1
                                            
                                            # 통계 업데이트
                                            stats["by_type"][prop_name] = stats["by_type"].get(prop_name, 0) + 1
                                            stats["by_trade"][trade_name] = stats["by_trade"].get(trade_name, 0) + 1
                                    else:
                                        stats["duplicates"] += 1
                                
                                # 진행 표시
                                if page % 5 == 0:
                                    print(f"    페이지 {page}: 누적 {combo_count}개", end="\r")
                                
                                # 마지막 페이지 체크
                                if not data.get("more", False) or len(items) < 20:
                                    break
                            else:
                                break
                                
                    except Exception as e:
                        # 에러는 조용히 처리
                        break
                    
                    # Rate limiting
                    await asyncio.sleep(0.2)
                
                if combo_count > 0:
                    print(f"    ✅ {combo_count}개 수집 완료")
                    
                stats["total"] = len(all_properties)
                
                # 실시간 진행 상황
                print(f"    📊 현재까지 총: {stats['total']:,}개 수집")
                
                # 8000개 넘으면 조기 종료 옵션
                if stats["total"] > 8000:
                    print(f"\n🎯 목표 달성! 8000개 이상 수집 완료")
                    break
            
            if stats["total"] > 8000:
                break
        
        return all_properties, stats
    
    def _parse_article_enhanced(self, article_data, prop_type, trade_type):
        """개선된 파싱"""
        try:
            # 가격 처리
            price = article_data.get("prc", "0")
            if isinstance(price, str):
                price = int(price.replace(",", "")) if price and price != "-" else 0
            
            # 면적 처리
            area = article_data.get("spc1", article_data.get("spc", "0"))
            if isinstance(area, str):
                try:
                    area = float(area) if area and area != "-" else 0
                except:
                    area = 0
            
            # 추가 정보
            tags = article_data.get("tagList", [])
            
            return {
                "type": prop_type,
                "trade_type": trade_type,
                "article_id": str(article_data.get("atclNo", "")),
                "title": article_data.get("atclNm", ""),
                "address": article_data.get("cortarNm", "삼성1동"),
                "price": price,
                "area": area,
                "floor": article_data.get("flrInfo", ""),
                "direction": article_data.get("direction", ""),
                "lat": article_data.get("lat", 0),
                "lon": article_data.get("lng", article_data.get("lon", 0)),
                "realtor": article_data.get("rltrNm", ""),
                "description": article_data.get("atclFetrDesc", ""),
                "tags": tags,
                "naver_link": f"https://m.land.naver.com/article/info/{article_data.get('atclNo')}",
                "collected_at": datetime.now().isoformat()
            }
        except Exception:
            return None


async def main():
    """메인 실행"""
    
    start_time = time.time()
    
    async with MaxNaverCollector() as collector:
        properties, stats = await collector.collect_all_properties()
    
    elapsed = time.time() - start_time
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 최종 수집 결과")
    print("=" * 70)
    print(f"✅ 전체 매물: {stats['total']:,}개")
    print(f"🔄 중복 제거: {stats['duplicates']:,}개")
    print(f"⏱️ 소요 시간: {elapsed/60:.1f}분")
    
    print("\n📈 매물 유형별:")
    for prop_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  - {prop_type}: {count:,}개")
    
    print("\n💰 거래 유형별:")
    for trade_type, count in stats['by_trade'].items():
        if count > 0:
            print(f"  - {trade_type}: {count:,}개")
    
    # 가격 분석
    sale_props = [p for p in properties if p['trade_type'] == '매매' and p['price'] > 0]
    if sale_props:
        prices = [p['price'] for p in sale_props]
        print(f"\n💵 매매가 분석 ({len(sale_props):,}개):")
        print(f"  - 평균: {sum(prices)/len(prices):,.0f}만원")
        print(f"  - 최저: {min(prices):,}만원")
        print(f"  - 최고: {max(prices):,}만원")
    
    # JSON 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"samsung1dong_all_{stats['total']}_{timestamp}.json"
    
    result_data = {
        "area": "강남구 삼성1동",
        "collection_time": datetime.now().isoformat(),
        "total_properties": stats['total'],
        "duplicates_removed": stats['duplicates'],
        "by_type": stats['by_type'],
        "by_trade": stats['by_trade'],
        "elapsed_minutes": elapsed/60,
        "properties": properties
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 데이터 저장: {filename}")
    
    # HTML 리포트
    create_full_report(result_data, timestamp)
    
    return stats['total']


def create_full_report(data, timestamp):
    """완전한 HTML 리포트 생성"""
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>삼성1동 전체 {data['total_properties']:,}개 매물</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 1600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 36px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .price {{ color: #e74c3c; font-weight: bold; }}
        .link {{ color: #3498db; text-decoration: none; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; }}
        .badge-apt {{ background: #3498db; }}
        .badge-ops {{ background: #9b59b6; }}
        .badge-vl {{ background: #e67e22; }}
        .badge-sale {{ background: #e74c3c; }}
        .badge-rent {{ background: #3498db; }}
        .badge-monthly {{ background: #f39c12; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 강남구 삼성1동 전체 매물 리포트</h1>
            <p style="font-size: 20px; margin: 10px 0;">총 {data['total_properties']:,}개 매물 수집 완료</p>
            <p>수집 시간: {data['collection_time']} | 소요 시간: {data.get('elapsed_minutes', 0):.1f}분</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{data['total_properties']:,}</div>
                <div class="stat-label">전체 매물</div>
            </div>
            <div class="stat">
                <div class="stat-number">{data.get('duplicates_removed', 0):,}</div>
                <div class="stat-label">중복 제거</div>
            </div>
    """
    
    for trade, count in data['by_trade'].items():
        html += f"""
            <div class="stat">
                <div class="stat-number">{count:,}</div>
                <div class="stat-label">{trade}</div>
            </div>
        """
    
    html += """
        </div>
        
        <h2>📋 매물 목록 (상위 1000개)</h2>
        <table>
            <thead>
                <tr>
                    <th>번호</th>
                    <th>유형</th>
                    <th>거래</th>
                    <th>매물명</th>
                    <th>가격</th>
                    <th>면적</th>
                    <th>층</th>
                    <th>주소</th>
                    <th>링크</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # 상위 1000개만 표시 (브라우저 성능)
    for i, prop in enumerate(data['properties'][:1000], 1):
        price = prop.get('price', 0)
        if price > 10000:
            price_str = f"{price/10000:.1f}억"
        else:
            price_str = f"{price:,}만원" if price else "-"
        
        prop_type = prop.get('type', '')
        badge_class = 'badge-apt' if '아파트' in prop_type else 'badge-ops' if '오피스텔' in prop_type else 'badge-vl'
        
        trade_type = prop.get('trade_type', '')
        trade_class = 'badge-sale' if '매매' in trade_type else 'badge-rent' if '전세' in trade_type else 'badge-monthly'
        
        html += f"""
            <tr>
                <td>{i}</td>
                <td><span class="badge {badge_class}">{prop_type}</span></td>
                <td><span class="badge {trade_class}">{trade_type}</span></td>
                <td>{prop.get('title', '-')}</td>
                <td class="price">{price_str}</td>
                <td>{prop.get('area', '-')}㎡</td>
                <td>{prop.get('floor', '-')}</td>
                <td>{prop.get('address', '삼성1동')}</td>
                <td><a href="{prop.get('naver_link', '#')}" target="_blank" class="link">보기</a></td>
            </tr>
        """
    
    html += f"""
            </tbody>
        </table>
        
        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <p>📌 전체 {data['total_properties']:,}개 중 상위 1000개만 표시됩니다.</p>
            <p>📌 전체 데이터는 JSON 파일에서 확인할 수 있습니다.</p>
        </div>
    </div>
</body>
</html>
    """
    
    filename = f"samsung1dong_all_{data['total_properties']}_{timestamp}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"📄 HTML 리포트: {filename}")


if __name__ == "__main__":
    asyncio.run(main())