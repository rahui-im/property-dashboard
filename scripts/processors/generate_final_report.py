#!/usr/bin/env python3
"""
최종 통합 리포트 생성기
멀티플랫폼 수집 결과를 HTML 형태로 종합 분석하여 시각화합니다.
"""

import json
import os
from datetime import datetime
from typing import Dict, List
import sys

# 한글 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

class FinalReportGenerator:
    """최종 리포트 생성기"""
    
    def __init__(self):
        self.target_count = 8000
        
    def generate_comprehensive_report(self):
        """종합 리포트 생성"""
        print("🏠 최종 통합 리포트 생성 시작...")
        
        # 1. 모든 데이터 파일 수집
        all_data = self._collect_all_data()
        
        # 2. 네이버 실제 데이터 추가
        naver_data = self._load_naver_real_data()
        if naver_data:
            all_data['naver_real'] = naver_data
            print(f"✅ 네이버 실제 데이터 추가: {len(naver_data)}개")
        
        # 3. 통계 분석
        statistics = self._analyze_comprehensive_stats(all_data)
        
        # 4. HTML 리포트 생성
        html_content = self._generate_html_report(all_data, statistics)
        
        # 5. 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_samsung1dong_report_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 최종 리포트 생성 완료: {filename}")
        
        # 6. 요약 출력
        self._print_summary(statistics)
        
        return filename
    
    def _collect_all_data(self):
        """모든 데이터 파일 수집"""
        all_data = {}
        
        # 통합 데이터 찾기
        integrated_files = [f for f in os.listdir('.') if f.startswith('integrated_samsung1dong') and f.endswith('.json')]
        if integrated_files:
            latest_file = max(integrated_files, key=lambda x: os.path.getmtime(x))
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data['integrated'] = data
                print(f"📂 통합 데이터 로드: {latest_file} ({data.get('total_properties', 0)}개)")
        
        # 플랫폼별 개별 데이터
        platforms = ['naver', 'zigbang', 'dabang', 'kb']
        
        for platform in platforms:
            platform_files = [f for f in os.listdir('.') if f.startswith(f'{platform}_samsung1dong') and f.endswith('.json')]
            
            if platform_files:
                latest_file = max(platform_files, key=lambda x: os.path.getmtime(x))
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data[platform] = data
                        count = len(data.get('properties', []))
                        print(f"📂 {platform} 데이터 로드: {latest_file} ({count}개)")
                except:
                    print(f"❌ {platform} 데이터 로드 실패: {latest_file}")
        
        return all_data
    
    def _load_naver_real_data(self):
        """네이버 실제 데이터 로드"""
        try:
            # 840개 네이버 데이터 파일 찾기
            naver_files = [f for f in os.listdir('.') if 'samsung1dong_full_' in f and f.endswith('.json')]
            
            if naver_files:
                latest_file = max(naver_files, key=lambda x: os.path.getmtime(x))
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('properties', [])
            
            return []
            
        except Exception as e:
            print(f"❌ 네이버 실제 데이터 로드 실패: {e}")
            return []
    
    def _analyze_comprehensive_stats(self, all_data):
        """종합 통계 분석"""
        stats = {
            'total_count': 0,
            'by_platform': {},
            'by_type': {},
            'by_price_range': {},
            'by_area_range': {},
            'price_stats': {},
            'area_stats': {},
            'data_quality': {},
            'achievement_rate': 0
        }
        
        # 각 플랫폼별 통계
        for platform, data in all_data.items():
            if platform == 'integrated':
                continue
                
            # 데이터가 리스트인 경우와 딕셔너리인 경우 처리
            if isinstance(data, list):
                properties = data
            else:
                properties = data.get('properties', [])
                
            count = len(properties)
            stats['by_platform'][platform] = count
            stats['total_count'] += count
            
            # 데이터 품질 분석
            quality_score = self._calculate_quality_score(properties)
            stats['data_quality'][platform] = quality_score
            
            # 매물 유형별 분석
            for prop in properties:
                prop_type = prop.get('type', '기타')
                stats['by_type'][prop_type] = stats['by_type'].get(prop_type, 0) + 1
                
                # 가격 범위별
                price = prop.get('price', 0)
                price_range = self._get_price_range(price)
                stats['by_price_range'][price_range] = stats['by_price_range'].get(price_range, 0) + 1
                
                # 면적 범위별
                area = prop.get('area', 0)
                area_range = self._get_area_range(area)
                stats['by_area_range'][area_range] = stats['by_area_range'].get(area_range, 0) + 1
        
        # 달성률 계산
        stats['achievement_rate'] = (stats['total_count'] / self.target_count) * 100
        
        # 가격/면적 통계
        all_prices = []
        all_areas = []
        
        for platform, data in all_data.items():
            if platform == 'integrated':
                continue
                
            # 데이터가 리스트인 경우와 딕셔너리인 경우 처리
            if isinstance(data, list):
                properties = data
            else:
                properties = data.get('properties', [])
                
            for prop in properties:
                price = prop.get('price', 0)
                area = prop.get('area', 0)
                
                if price > 0:
                    all_prices.append(price)
                if area > 0:
                    all_areas.append(area)
        
        if all_prices:
            stats['price_stats'] = {
                'min': min(all_prices),
                'max': max(all_prices),
                'avg': sum(all_prices) / len(all_prices),
                'median': sorted(all_prices)[len(all_prices) // 2]
            }
        
        if all_areas:
            stats['area_stats'] = {
                'min': min(all_areas),
                'max': max(all_areas),
                'avg': sum(all_areas) / len(all_areas),
                'median': sorted(all_areas)[len(all_areas) // 2]
            }
        
        return stats
    
    def _calculate_quality_score(self, properties):
        """데이터 품질 점수 계산"""
        if not properties:
            return 0
        
        total_score = 0
        for prop in properties:
            score = 0
            if prop.get('title'): score += 1
            if prop.get('address'): score += 1
            if prop.get('price', 0) > 0: score += 1
            if prop.get('area', 0) > 0: score += 1
            if prop.get('lat') and prop.get('lng'): score += 2
            if prop.get('description'): score += 1
            if prop.get('url'): score += 1
            
            total_score += score
        
        return (total_score / (len(properties) * 8)) * 100  # 최대 8점
    
    def _get_price_range(self, price):
        """가격 범위 분류"""
        if price <= 10000:
            return "1억 이하"
        elif price <= 30000:
            return "1억-3억"
        elif price <= 50000:
            return "3억-5억"
        elif price <= 100000:
            return "5억-10억"
        else:
            return "10억 초과"
    
    def _get_area_range(self, area):
        """면적 범위 분류"""
        if area <= 40:
            return "40㎡ 이하"
        elif area <= 60:
            return "40-60㎡"
        elif area <= 85:
            return "60-85㎡"
        elif area <= 120:
            return "85-120㎡"
        else:
            return "120㎡ 초과"
    
    def _generate_html_report(self, all_data, statistics):
        """HTML 리포트 생성"""
        
        # 플랫폼 데이터 준비
        platform_data = []
        for platform, data in all_data.items():
            if platform == 'integrated':
                continue
                
            # 데이터가 리스트인 경우와 딕셔너리인 경우 처리
            if isinstance(data, list):
                properties = data
            else:
                properties = data.get('properties', [])
                
            platform_info = {
                'name': platform,
                'display_name': self._get_platform_display_name(platform),
                'count': len(properties),
                'quality': statistics['data_quality'].get(platform, 0),
                'sample_properties': properties[:5]  # 샘플 5개
            }
            platform_data.append(platform_info)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>강남구 삼성1동 매물 수집 최종 리포트</title>
    <style>
        body {{
            font-family: 'Segoe UI', 'Noto Sans KR', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 1.1em;
        }}
        .summary-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        .summary-card .unit {{
            color: #666;
            font-size: 0.9em;
        }}
        .achievement {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 10px;
        }}
        .achievement h2 {{
            margin: 0 0 10px 0;
        }}
        .progress-bar {{
            background: rgba(255,255,255,0.3);
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 15px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: white;
            border-radius: 10px;
            transition: width 0.3s ease;
            width: {min(statistics['achievement_rate'], 100)}%;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .platform-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .platform-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .platform-header {{
            background: #667eea;
            color: white;
            padding: 15px;
            font-weight: bold;
        }}
        .platform-content {{
            padding: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .property-sample {{
            background: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .property-title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .property-details {{
            color: #666;
            font-size: 0.9em;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin: 20px 0;
        }}
        .status-success {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-danger {{ color: #dc3545; }}
        .footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 강남구 삼성1동 매물 수집 리포트</h1>
            <p>멀티플랫폼 통합 수집 결과 분석</p>
            <p>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
        </div>
        
        <div class="content">
            <!-- 요약 섹션 -->
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>총 수집 매물</h3>
                    <div class="number">{statistics['total_count']:,}</div>
                    <div class="unit">개</div>
                </div>
                <div class="summary-card">
                    <h3>목표 달성률</h3>
                    <div class="number">{statistics['achievement_rate']:.1f}</div>
                    <div class="unit">%</div>
                </div>
                <div class="summary-card">
                    <h3>플랫폼 수</h3>
                    <div class="number">{len(statistics['by_platform'])}</div>
                    <div class="unit">개</div>
                </div>
                <div class="summary-card">
                    <h3>매물 유형</h3>
                    <div class="number">{len(statistics['by_type'])}</div>
                    <div class="unit">개</div>
                </div>
            </div>
            
            <!-- 목표 달성률 -->
            <div class="achievement">
                <h2>목표 달성률</h2>
                <div style="font-size: 1.2em;">
                    {statistics['total_count']:,}개 / {self.target_count:,}개 
                    {'✅ 달성' if statistics['total_count'] >= self.target_count else '❌ 미달성'}
                </div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div>{statistics['achievement_rate']:.1f}% 완료</div>
            </div>
            
            <!-- 플랫폼별 결과 -->
            <div class="section">
                <h2>📊 플랫폼별 수집 결과</h2>
                <div class="platform-grid">
        """
        
        # 플랫폼별 카드 생성
        for platform in platform_data:
            status_class = "status-success" if platform['count'] > 0 else "status-danger"
            
            html_content += f"""
                    <div class="platform-card">
                        <div class="platform-header">
                            {platform['display_name']}
                        </div>
                        <div class="platform-content">
                            <div class="stats-grid">
                                <div class="stat-item">
                                    <div class="stat-label">수집 매물</div>
                                    <div class="stat-value {status_class}">{platform['count']:,}개</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-label">데이터 품질</div>
                                    <div class="stat-value">{platform['quality']:.1f}%</div>
                                </div>
                            </div>
                            
                            <h4>샘플 매물</h4>
            """
            
            # 샘플 매물 표시
            for prop in platform['sample_properties']:
                price_text = f"{prop.get('price', 0):,}만원" if prop.get('price', 0) > 0 else "가격 미정"
                area_text = f"{prop.get('area', 0):.1f}㎡" if prop.get('area', 0) > 0 else "면적 미정"
                
                html_content += f"""
                            <div class="property-sample">
                                <div class="property-title">{prop.get('title', '제목 없음')}</div>
                                <div class="property-details">
                                    {prop.get('type', '기타')} | {price_text} | {area_text}<br>
                                    📍 {prop.get('address', '주소 미정')}
                                </div>
                            </div>
                """
            
            html_content += """
                        </div>
                    </div>
            """
        
        # 통계 차트 섹션
        html_content += f"""
                </div>
            </div>
            
            <!-- 통계 분석 -->
            <div class="section">
                <h2>📈 통계 분석</h2>
                
                <div class="chart-container">
                    <h3>매물 유형별 분포</h3>
                    <div class="stats-grid">
        """
        
        # 매물 유형별 통계
        for prop_type, count in statistics['by_type'].items():
            percentage = (count / statistics['total_count']) * 100 if statistics['total_count'] > 0 else 0
            html_content += f"""
                        <div class="stat-item">
                            <div class="stat-label">{prop_type}</div>
                            <div class="stat-value">{count:,}개</div>
                            <div class="unit">({percentage:.1f}%)</div>
                        </div>
            """
        
        html_content += """
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>가격대별 분포</h3>
                    <div class="stats-grid">
        """
        
        # 가격대별 통계
        for price_range, count in statistics['by_price_range'].items():
            percentage = (count / statistics['total_count']) * 100 if statistics['total_count'] > 0 else 0
            html_content += f"""
                        <div class="stat-item">
                            <div class="stat-label">{price_range}</div>
                            <div class="stat-value">{count:,}개</div>
                            <div class="unit">({percentage:.1f}%)</div>
                        </div>
            """
        
        html_content += """
                    </div>
                </div>
            </div>
            
            <!-- 데이터 품질 -->
            <div class="section">
                <h2>🔍 데이터 품질 분석</h2>
                <div class="stats-grid">
        """
        
        # 데이터 품질 분석
        for platform, quality in statistics['data_quality'].items():
            status_class = "status-success" if quality >= 80 else "status-warning" if quality >= 60 else "status-danger"
            html_content += f"""
                    <div class="stat-item">
                        <div class="stat-label">{self._get_platform_display_name(platform)} 품질</div>
                        <div class="stat-value {status_class}">{quality:.1f}%</div>
                    </div>
            """
        
        # 가격/면적 통계
        if statistics['price_stats']:
            html_content += f"""
                    <div class="stat-item">
                        <div class="stat-label">평균 가격</div>
                        <div class="stat-value">{statistics['price_stats']['avg']:,.0f}만원</div>
                    </div>
            """
        
        if statistics['area_stats']:
            html_content += f"""
                    <div class="stat-item">
                        <div class="stat-label">평균 면적</div>
                        <div class="stat-value">{statistics['area_stats']['avg']:.1f}㎡</div>
                    </div>
            """
        
        html_content += f"""
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 부동산 매물 수집 시스템 | 생성일시: {datetime.now().isoformat()}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _get_platform_display_name(self, platform):
        """플랫폼 표시명 반환"""
        display_names = {
            'naver': '네이버 부동산',
            'naver_real': '네이버 부동산 (실제)',
            'zigbang': '직방',
            'dabang': '다방',
            'kb': 'KB부동산'
        }
        return display_names.get(platform, platform.title())
    
    def _print_summary(self, statistics):
        """요약 출력"""
        print("\n" + "="*60)
        print("📊 최종 수집 결과 요약")
        print("="*60)
        print(f"🎯 목표: {self.target_count:,}개")
        print(f"📦 수집: {statistics['total_count']:,}개")
        print(f"📈 달성률: {statistics['achievement_rate']:.1f}%")
        
        print("\n📊 플랫폼별 수집 현황:")
        for platform, count in statistics['by_platform'].items():
            display_name = self._get_platform_display_name(platform)
            quality = statistics['data_quality'].get(platform, 0)
            print(f"  📊 {display_name}: {count:,}개 (품질: {quality:.1f}%)")
        
        print("\n🏠 매물 유형별 분포:")
        for prop_type, count in statistics['by_type'].items():
            percentage = (count / statistics['total_count']) * 100 if statistics['total_count'] > 0 else 0
            print(f"  📊 {prop_type}: {count:,}개 ({percentage:.1f}%)")
        
        if statistics['total_count'] >= self.target_count:
            print(f"\n🎉 목표 달성! {statistics['total_count']:,}개 >= {self.target_count:,}개")
        else:
            shortage = self.target_count - statistics['total_count']
            print(f"\n❌ 목표 미달성: {statistics['total_count']:,}개 < {self.target_count:,}개 (부족: {shortage:,}개)")


def main():
    """메인 함수"""
    print("🏠 최종 통합 리포트 생성기 시작")
    
    generator = FinalReportGenerator()
    report_filename = generator.generate_comprehensive_report()
    
    print(f"\n✅ 최종 리포트 생성 완료!")
    print(f"📄 파일명: {report_filename}")
    print(f"🌐 브라우저에서 열어보세요: file://{os.path.abspath(report_filename)}")


if __name__ == "__main__":
    main()