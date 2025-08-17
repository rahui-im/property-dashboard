"""
네이버 부동산 수집 에이전트
MCP 오케스트레이터와 통신하며 네이버 부동산 데이터 수집
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List
from datetime import datetime
import websockets
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.mcp.collectors.naver_mobile_collector import (
    NaverMobileCollector,
    PropertyType,
    TradeType
)

logger = logging.getLogger(__name__)


class NaverCollectorAgent:
    """네이버 부동산 수집 에이전트"""
    
    def __init__(self, agent_id: str = "naver_collector_01"):
        self.agent_id = agent_id
        self.orchestrator_url = "ws://localhost:8765"
        self.collector = None
        self.running = False
        self.websocket = None
        
    async def start(self):
        """에이전트 시작"""
        logger.info(f"Starting {self.agent_id}")
        self.running = True
        
        while self.running:
            try:
                await self.connect_to_orchestrator()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)
                
    async def connect_to_orchestrator(self):
        """오케스트레이터 연결"""
        try:
            async with websockets.connect(self.orchestrator_url) as websocket:
                self.websocket = websocket
                logger.info(f"Connected to orchestrator")
                
                # 에이전트 등록
                await self.register_agent()
                
                # 메시지 수신 루프
                async for message in websocket:
                    await self.handle_message(message)
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            raise
            
    async def register_agent(self):
        """오케스트레이터에 에이전트 등록"""
        registration = {
            "type": "register",
            "agent_id": self.agent_id,
            "agent_type": "collector",
            "platform": "naver",
            "capabilities": {
                "property_types": [pt.value for pt in PropertyType],
                "trade_types": [tt.value for tt in TradeType],
                "batch_size": 100,
                "rate_limit": "1req/sec"
            },
            "status": "ready"
        }
        
        await self.websocket.send(json.dumps(registration))
        logger.info(f"Agent {self.agent_id} registered")
        
    async def handle_message(self, message: str):
        """오케스트레이터 메시지 처리"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "task":
                await self.handle_task(data)
            elif msg_type == "ping":
                await self.send_pong()
            elif msg_type == "stop":
                await self.stop()
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid message format: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
    async def handle_task(self, task_data: Dict[str, Any]):
        """수집 작업 처리"""
        task_id = task_data.get("task_id")
        task_type = task_data.get("task_type")
        params = task_data.get("params", {})
        
        logger.info(f"Processing task {task_id}: {task_type}")
        
        # 작업 시작 알림
        await self.send_status(task_id, "processing")
        
        try:
            if task_type == "collect_area":
                result = await self.collect_area(params)
            elif task_type == "collect_complex":
                result = await self.collect_complex(params)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
            # 결과 전송
            await self.send_result(task_id, result)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self.send_error(task_id, str(e))
            
    async def collect_area(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """지역별 매물 수집
        
        Args:
            params: 수집 파라미터
                - area: 지역명
                - property_types: 매물 유형 리스트
                - trade_type: 거래 유형
                
        Returns:
            수집 결과
        """
        area = params.get("area")
        property_types = params.get("property_types", ["아파트", "오피스텔", "빌라"])
        trade_type = params.get("trade_type", "매매")
        
        # PropertyType Enum으로 변환
        prop_types = []
        for pt_str in property_types:
            for pt in PropertyType:
                if pt.value == pt_str:
                    prop_types.append(pt)
                    break
                    
        # TradeType Enum으로 변환
        tt = TradeType.SALE
        for trade in TradeType:
            if trade.value == trade_type:
                tt = trade
                break
                
        # 수집 실행
        async with NaverMobileCollector() as collector:
            results = await collector.search_area(
                area=area,
                property_types=prop_types,
                trade_type=tt
            )
            
        return {
            "platform": "naver",
            "area": area,
            "property_count": len(results.get("properties", [])),
            "properties": results.get("properties", []),
            "collected_at": datetime.now().isoformat()
        }
        
    async def collect_complex(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """특정 단지 상세 정보 수집
        
        Args:
            params: 수집 파라미터
                - complex_id: 단지 ID
                - property_type: 매물 유형
                
        Returns:
            수집 결과
        """
        # TODO: 단지 상세 정보 수집 구현
        pass
        
    async def send_status(self, task_id: str, status: str):
        """작업 상태 전송"""
        message = {
            "type": "status",
            "agent_id": self.agent_id,
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        await self.websocket.send(json.dumps(message))
        
    async def send_result(self, task_id: str, result: Dict[str, Any]):
        """작업 결과 전송"""
        message = {
            "type": "result",
            "agent_id": self.agent_id,
            "task_id": task_id,
            "result": result,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        await self.websocket.send(json.dumps(message))
        logger.info(f"Task {task_id} completed")
        
    async def send_error(self, task_id: str, error: str):
        """에러 전송"""
        message = {
            "type": "error",
            "agent_id": self.agent_id,
            "task_id": task_id,
            "error": error,
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
        await self.websocket.send(json.dumps(message))
        
    async def send_pong(self):
        """Pong 응답"""
        message = {
            "type": "pong",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.websocket.send(json.dumps(message))
        
    async def stop(self):
        """에이전트 중지"""
        logger.info(f"Stopping {self.agent_id}")
        self.running = False
        if self.websocket:
            await self.websocket.close()


async def main():
    """메인 실행 함수"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 한글 인코딩 설정
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    # 에이전트 실행
    agent = NaverCollectorAgent()
    await agent.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed: {e}")