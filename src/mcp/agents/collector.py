"""
매물 수집 서브에이전트 - MCP 클라이언트
"""
import asyncio
import aiohttp
import json
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.mcp.collectors.naver_collector import NaverCollector
from src.mcp.collectors.zigbang_collector import ZigbangCollector
from src.mcp.collectors.dabang_collector import DabangCollector

logger.add("logs/collector_agent_{time}.log", rotation="1 day")


class CollectorAgent:
    """매물 수집 서브에이전트"""
    
    def __init__(self, mcp_server_url: str = "ws://localhost:9001/mcp/ws"):
        self.mcp_server_url = mcp_server_url
        self.agent_id = None
        self.ws = None
        self.collectors = {
            'naver': NaverCollector(),
            'zigbang': ZigbangCollector(),
            'dabang': DabangCollector()
        }
        self.running_tasks = {}
        
    async def connect(self):
        """MCP 서버에 연결"""
        session = aiohttp.ClientSession()
        self.ws = await session.ws_connect(self.mcp_server_url)
        
        # 에이전트 등록
        await self.register()
        
        logger.info(f"Connected to MCP server: {self.mcp_server_url}")
        
    async def register(self):
        """에이전트 등록"""
        message = {
            "type": "request",
            "id": "register",
            "method": "agent.register",
            "params": {
                "type": "collector",
                "platforms": list(self.collectors.keys()),
                "capabilities": [
                    "async_collection",
                    "rate_limiting",
                    "dynamic_rendering"
                ]
            }
        }
        
        await self.ws.send_json(message)
        response = await self.ws.receive_json()
        self.agent_id = response.get('params', {}).get('result', {}).get('agent_id')
        logger.info(f"Agent registered with ID: {self.agent_id}")
        
    async def listen(self):
        """서버로부터 메시지 수신 대기"""
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self.handle_message(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {self.ws.exception()}')
                break
                
    async def handle_message(self, message: dict):
        """메시지 처리"""
        method = message.get('method')
        params = message.get('params', {})
        
        logger.info(f"Received message: {method}")
        
        if method == 'collect':
            await self.handle_collect(params)
        elif method == 'stop':
            await self.handle_stop(params)
        elif method == 'status':
            await self.send_status(params)
            
    async def handle_collect(self, params: dict):
        """수집 요청 처리"""
        task_id = params.get('task_id')
        platform = params.get('platform')
        areas = params.get('areas', [])
        
        logger.info(f"Starting collection task {task_id} for {platform} in {areas}")
        
        # 비동기 수집 작업 시작
        if platform == 'all':
            # 모든 플랫폼에서 수집
            for plat_name, collector in self.collectors.items():
                task = asyncio.create_task(
                    self.collect_from_platform(task_id, plat_name, collector, areas)
                )
                self.running_tasks[f"{task_id}_{plat_name}"] = task
        else:
            # 특정 플랫폼에서만 수집
            if platform in self.collectors:
                collector = self.collectors[platform]
                task = asyncio.create_task(
                    self.collect_from_platform(task_id, platform, collector, areas)
                )
                self.running_tasks[f"{task_id}_{platform}"] = task
                
    async def collect_from_platform(self, task_id: str, platform: str, 
                                   collector, areas: List[str]):
        """플랫폼별 수집 실행"""
        all_properties = []
        
        for area in areas:
            try:
                logger.info(f"Collecting from {platform} for {area}...")
                properties = await collector.collect(area)
                
                # 수집된 데이터에 메타데이터 추가
                for prop in properties:
                    prop['task_id'] = task_id
                    prop['platform'] = platform
                    prop['area'] = area
                    prop['collected_at'] = datetime.now().isoformat()
                    
                all_properties.extend(properties)
                
                # 진행 상황 보고
                await self.report_progress(task_id, platform, area, len(properties))
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting from {platform} for {area}: {e}")
                await self.report_error(task_id, platform, area, str(e))
                
        # 수집 완료 보고
        await self.report_completion(task_id, platform, all_properties)
        
    async def report_progress(self, task_id: str, platform: str, 
                             area: str, count: int):
        """진행 상황 보고"""
        message = {
            "type": "notification",
            "id": f"progress_{task_id}",
            "method": "collect.progress",
            "params": {
                "task_id": task_id,
                "platform": platform,
                "area": area,
                "collected_count": count,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.ws.send_json(message)
        
    async def report_completion(self, task_id: str, platform: str, 
                               properties: List[Dict]):
        """수집 완료 보고"""
        message = {
            "type": "notification",
            "id": f"complete_{task_id}",
            "method": "collect.complete",
            "params": {
                "task_id": task_id,
                "platform": platform,
                "total_collected": len(properties),
                "data": properties,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.ws.send_json(message)
        
    async def report_error(self, task_id: str, platform: str, 
                          area: str, error: str):
        """에러 보고"""
        message = {
            "type": "notification",
            "id": f"error_{task_id}",
            "method": "collect.error",
            "params": {
                "task_id": task_id,
                "platform": platform,
                "area": area,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.ws.send_json(message)
        
    async def handle_stop(self, params: dict):
        """수집 중지 처리"""
        task_id = params.get('task_id')
        
        # 해당 작업 중지
        tasks_to_stop = [
            key for key in self.running_tasks.keys() 
            if key.startswith(task_id)
        ]
        
        for task_key in tasks_to_stop:
            if task_key in self.running_tasks:
                self.running_tasks[task_key].cancel()
                del self.running_tasks[task_key]
                
        logger.info(f"Stopped tasks for {task_id}")
        
    async def send_status(self, params: dict):
        """상태 정보 전송"""
        status = {
            "agent_id": self.agent_id,
            "type": "collector",
            "running_tasks": len(self.running_tasks),
            "platforms": list(self.collectors.keys()),
            "status": "active"
        }
        
        message = {
            "type": "response",
            "id": params.get('id'),
            "method": "agent.status",
            "params": {"result": status}
        }
        
        await self.ws.send_json(message)
        
    async def run(self):
        """에이전트 실행"""
        try:
            await self.connect()
            await self.listen()
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            if self.ws:
                await self.ws.close()


async def main():
    """메인 실행 함수"""
    agent = CollectorAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())