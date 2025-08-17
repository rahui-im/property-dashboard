"""
매물 수집 에이전트 - 메인 실행 파일
실행 방법: python main.py
"""
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# 환경 변수 로드
load_dotenv()

# 로그 설정
logger.add("logs/collector_{time}.log", rotation="1 day")

# src 폴더를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.collectors.simple_collector import SimplePropertyCollector
from src.processors.excel_manager import ExcelManager

def main():
    """메인 실행 함수"""
    logger.info("🚀 매물 수집 에이전트 시작!")
    
    # 수집기 초기화
    collector = SimplePropertyCollector()
    excel_manager = ExcelManager()
    
    # 수집할 지역 목록
    areas = ["강남구", "서초구", "송파구"]
    
    try:
        for area in areas:
            logger.info(f"📍 {area} 매물 수집 시작...")
            
            # 매물 수집
            properties = collector.collect(area)
            
            if properties:
                # Excel 파일로 저장
                filename = excel_manager.save_properties(properties, area)
                logger.success(f"✅ {area}: {len(properties)}개 매물 저장 완료 → {filename}")
            else:
                logger.warning(f"⚠️ {area}: 수집된 매물이 없습니다.")
            
            # 과부하 방지를 위한 대기
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
    
    logger.info("🏁 매물 수집 완료!")

if __name__ == "__main__":
    main()