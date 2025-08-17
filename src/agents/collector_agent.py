"""
수집 에이전트 - 플랫폼별 매물 수집 담당
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import aiohttp
from loguru import logger
import uuid

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.collectors.naver_collector import NaverCollector
from mcp.collectors.zigbang_collector import ZigbangCollector
from mcp.collectors.dabang_collector import DabangCollector


class CollectorAgent:
    """수집 에이전트 메인 클래스"""
    
    def __init__(self, platform: str = None, orchestrator_url: str = None):
        self.platform = platform or os.getenv('PLATFORM', 'naver')
        self.orchestrator_url = orchestrator_url or os.getenv('ORCHESTRATOR_URL', 'http://localhost:8000')
        self.agent_id = str(uuid.uuid4())
        self.agent_type = 'collector'
        
        # 플랫폼별 수집기 초기화
        self.collector = self._init_collector()
        
        # WebSocket 연결
        self.ws = None
        self.session = None
        self.running = False
        
        # 로거 설정
        logger.add(f"logs/collector_{self.platform}_{self.agent_id}.log", rotation="1 day")
        
    def _init_collector(self):
        """플랫폼별 수집기 초기화"""
        collectors = {
            'naver': NaverCollector,
            'zigbang': ZigbangCollector,
            'dabang': DabangCollector
        }
        
        collector_class = collectors.get(self.platform)
        if not collector_class:
            raise ValueError(f"Unsupported platform: {self.platform}")
            
        return collector_class()
        
    async def start(self):
        """에이전트 시작"""
        logger.info(f"Starting collector agent for {self.platform}")
        self.running = True
        
        try:
            # 오케스트레이터에 등록
            await self.register()
            
            # WebSocket 연결
            await self.connect_websocket()
            
            # 메시지 수신 루프
            await self.message_loop()
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            await self.cleanup()
            
    async def register(self):
        """오케스트레이터에 에이전트 등록"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        registration_data = {
            'type': self.agent_type,
            'platform': self.platform,
            'capabilities': self._get_capabilities()
        }
        
        try:
            async with self.session.post(
                f"{self.orchestrator_url}/api/v1/agents/register",
                json=registration_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.agent_id = result.get('agent_id', self.agent_id)
                    logger.info(f"Agent registered: {self.agent_id}")
                else:
                    logger.error(f"Registration failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Registration error: {e}")
            
    def _get_capabilities(self) -> List[str]:
        """에이전트 능력 반환"""
        base_capabilities = [
            'collect',
            'validate',
            'rate_limit',
            'proxy_support'
        ]
        
        # 플랫폼별 특수 능력
        platform_capabilities = {
            'naver': ['dynamic_rendering', 'api_support'],
            'zigbang': ['api_support', 'batch_processing'],
            'dabang': ['coordinate_search', 'room_types']
        }
        
        return base_capabilities + platform_capabilities.get(self.platform, [])
        
    async def connect_websocket(self):
        """WebSocket 연결"""
        ws_url = self.orchestrator_url.replace('http', 'ws') + f'/ws/{self.agent_id}'
        
        try:
            self.ws = await self.session.ws_connect(ws_url)
            logger.info(f"WebSocket connected to {ws_url}")
            
            # 하트비트 시작
            asyncio.create_task(self.heartbeat_loop())
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
            
    async def heartbeat_loop(self):
        """하트비트 전송"""
        while self.running and self.ws:
            try:
                await self.ws.send_json({
                    'type': 'heartbeat',
                    'agent_id': self.agent_id,
                    'timestamp': datetime.now().isoformat()
                })
                await asyncio.sleep(30)  # 30초마다
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
                
    async def message_loop(self):
        """메시지 수신 및 처리"""
        while self.running and self.ws:
            try:
                msg = await self.ws.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_message(data)
                    
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.ws.exception()}")
                    break
                    
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket closed")
                    break
                    
            except Exception as e:
                logger.error(f"Message loop error: {e}")
                
    async def handle_message(self, message: dict):
        """메시지 처리"""
        msg_type = message.get('type')
        
        if msg_type == 'task_assignment':
            await self.handle_task_assignment(message)
        elif msg_type == 'cancel_task':
            await self.handle_task_cancellation(message)
        elif msg_type == 'status_request':
            await self.send_status()
            
    async def handle_task_assignment(self, message: dict):
        """작업 할당 처리"""
        subtask_id = message.get('subtask_id')
        area = message.get('area')
        filters = message.get('filters', {})
        max_items = message.get('max_items', 100)
        
        logger.info(f"Received task {subtask_id}: {self.platform} - {area}")
        
        try:
            # 상태를 BUSY로 변경
            await self.update_status('busy')
            
            # 매물 수집 실행
            async with self.collector as collector:
                properties = await collector.collect(
                    area=area,
                    **filters,
                    max_items=max_items
                )
                
            # 결과 전송
            await self.send_result(subtask_id, properties)
            
            logger.info(f"Task {subtask_id} completed: {len(properties)} items collected")
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            await self.send_error(subtask_id, str(e))
            
        finally:
            # 상태를 IDLE로 변경
            await self.update_status('idle')
            
    async def send_result(self, subtask_id: str, properties: List[Dict]):
        """작업 결과 전송"""
        result_message = {
            'type': 'task_result',
            'subtask_id': subtask_id,
            'agent_id': self.agent_id,
            'result': {
                'platform': self.platform,
                'data': properties,
                'collected_at': datetime.now().isoformat(),
                'count': len(properties)
            }
        }
        
        if self.ws:
            await self.ws.send_json(result_message)
            
    async def send_error(self, subtask_id: str, error_message: str):
        """에러 전송"""
        error_msg = {
            'type': 'error',
            'subtask_id': subtask_id,
            'agent_id': self.agent_id,
            'error_type': 'task_failure',
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.ws:
            await self.ws.send_json(error_msg)
            
    async def update_status(self, status: str):
        """상태 업데이트"""
        status_message = {
            'type': 'agent_status',
            'agent_id': self.agent_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.ws:
            await self.ws.send_json(status_message)
            
    async def send_status(self):
        """현재 상태 전송"""
        status = {
            'type': 'status_response',
            'agent_id': self.agent_id,
            'platform': self.platform,
            'status': 'running' if self.running else 'stopped',
            'capabilities': self._get_capabilities(),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.ws:
            await self.ws.send_json(status)
            
    async def handle_task_cancellation(self, message: dict):
        """작업 취소 처리"""
        subtask_id = message.get('subtask_id')
        logger.info(f"Cancelling task {subtask_id}")
        # 실제 취소 로직 구현
        
    async def cleanup(self):
        """정리 작업"""
        self.running = False
        
        if self.ws:
            await self.ws.close()
            
        if self.session:
            await self.session.close()
            
        logger.info("Agent cleanup completed")
        
    async def run(self):
        """에이전트 실행"""
        await self.start()


async def main():
    """메인 함수"""
    # 환경 변수에서 플랫폼 읽기
    platform = os.getenv('PLATFORM', 'naver')
    orchestrator_url = os.getenv('ORCHESTRATOR_URL', 'http://localhost:8000')
    
    # 에이전트 생성 및 실행
    agent = CollectorAgent(platform, orchestrator_url)
    
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())