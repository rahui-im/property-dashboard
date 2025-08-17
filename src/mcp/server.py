"""
MCP 서버 - 부동산 매물 수집 오케스트레이터
"""
import asyncio
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
from loguru import logger
from aiohttp import web
import aiohttp_cors

# 로그 설정
logger.add("logs/mcp_server_{time}.log", rotation="1 day", level="INFO")

@dataclass
class MCPMessage:
    """MCP 메시지 형식"""
    type: str  # request, response, notification
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'MCPMessage':
        return cls(**json.loads(data))


class MCPServer:
    """MCP 서버 메인 클래스"""
    
    def __init__(self, host: str = "localhost", port: int = 9001):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.agents = {}  # 연결된 에이전트들
        self.tasks = {}   # 실행 중인 작업들
        self.setup_routes()
        self.setup_cors()
        
    def setup_routes(self):
        """라우트 설정"""
        self.app.router.add_post('/mcp/request', self.handle_request)
        self.app.router.add_get('/mcp/status', self.handle_status)
        self.app.router.add_get('/mcp/agents', self.handle_list_agents)
        self.app.router.add_websocket('/mcp/ws', self.websocket_handler)
        
    def setup_cors(self):
        """CORS 설정"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def handle_request(self, request: web.Request) -> web.Response:
        """MCP 요청 처리"""
        try:
            data = await request.json()
            msg = MCPMessage(
                type="request",
                id=data.get('id', str(uuid.uuid4())),
                method=data.get('method'),
                params=data.get('params', {})
            )
            
            logger.info(f"Received request: {msg.method} with params: {msg.params}")
            
            # 메서드별 처리
            result = await self.process_method(msg)
            
            response = MCPMessage(
                type="response",
                id=msg.id,
                method=msg.method,
                params={"result": result, "status": "success"}
            )
            
            return web.json_response(asdict(response))
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.json_response({
                "type": "response",
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def process_method(self, msg: MCPMessage) -> Dict[str, Any]:
        """메서드별 처리 로직"""
        method_parts = msg.method.split('.')
        category = method_parts[0]
        action = method_parts[1] if len(method_parts) > 1 else None
        
        if category == "collect":
            return await self.handle_collect(action, msg.params)
        elif category == "process":
            return await self.handle_process(action, msg.params)
        elif category == "store":
            return await self.handle_store(action, msg.params)
        elif category == "agent":
            return await self.handle_agent(action, msg.params)
        else:
            raise ValueError(f"Unknown method category: {category}")
    
    async def handle_collect(self, action: str, params: Dict) -> Dict:
        """수집 관련 처리"""
        if action == "start":
            # 수집 작업 시작
            task_id = str(uuid.uuid4())
            platform = params.get('platform', 'all')
            areas = params.get('areas', [])
            
            # 비동기 수집 작업 시작
            task = asyncio.create_task(self.start_collection(task_id, platform, areas))
            self.tasks[task_id] = task
            
            return {
                "task_id": task_id,
                "status": "started",
                "platform": platform,
                "areas": areas
            }
            
        elif action == "stop":
            # 수집 작업 중지
            task_id = params.get('task_id')
            if task_id in self.tasks:
                self.tasks[task_id].cancel()
                del self.tasks[task_id]
                return {"task_id": task_id, "status": "stopped"}
            return {"error": "Task not found"}
            
        elif action == "status":
            # 수집 상태 확인
            task_id = params.get('task_id')
            if task_id in self.tasks:
                task = self.tasks[task_id]
                return {
                    "task_id": task_id,
                    "status": "running" if not task.done() else "completed",
                    "done": task.done()
                }
            return {"error": "Task not found"}
    
    async def start_collection(self, task_id: str, platform: str, areas: list):
        """실제 수집 작업 실행"""
        logger.info(f"Starting collection task {task_id} for {platform} in {areas}")
        
        # 에이전트에게 수집 요청 전달
        for agent_id, agent in self.agents.items():
            if agent['type'] == 'collector' and (platform == 'all' or platform in agent['platforms']):
                await self.send_to_agent(agent_id, {
                    "method": "collect",
                    "params": {
                        "task_id": task_id,
                        "platform": platform,
                        "areas": areas
                    }
                })
        
        # 수집 완료 대기 (실제로는 더 복잡한 로직 필요)
        await asyncio.sleep(10)
        logger.info(f"Collection task {task_id} completed")
    
    async def handle_process(self, action: str, params: Dict) -> Dict:
        """데이터 처리 관련"""
        if action == "normalize":
            # 데이터 정규화
            data = params.get('data', [])
            normalized = await self.normalize_data(data)
            return {"count": len(normalized), "data": normalized}
            
        elif action == "validate":
            # 데이터 검증
            data = params.get('data', [])
            valid_data = await self.validate_data(data)
            return {"valid_count": len(valid_data), "data": valid_data}
            
        elif action == "deduplicate":
            # 중복 제거
            data = params.get('data', [])
            unique_data = await self.deduplicate_data(data)
            return {"unique_count": len(unique_data), "data": unique_data}
    
    async def handle_store(self, action: str, params: Dict) -> Dict:
        """저장 관련 처리"""
        if action == "save":
            # 데이터 저장
            data = params.get('data', [])
            storage_type = params.get('type', 'database')
            
            if storage_type == 'database':
                result = await self.save_to_database(data)
            elif storage_type == 'file':
                result = await self.save_to_file(data, params.get('format', 'json'))
            else:
                raise ValueError(f"Unknown storage type: {storage_type}")
                
            return {"saved_count": result['count'], "location": result['location']}
    
    async def handle_agent(self, action: str, params: Dict) -> Dict:
        """에이전트 관리"""
        if action == "register":
            # 에이전트 등록
            agent_id = str(uuid.uuid4())
            self.agents[agent_id] = {
                "id": agent_id,
                "type": params.get('type'),
                "platforms": params.get('platforms', []),
                "registered_at": datetime.now().isoformat()
            }
            return {"agent_id": agent_id, "status": "registered"}
            
        elif action == "unregister":
            # 에이전트 등록 해제
            agent_id = params.get('agent_id')
            if agent_id in self.agents:
                del self.agents[agent_id]
                return {"agent_id": agent_id, "status": "unregistered"}
            return {"error": "Agent not found"}
    
    async def websocket_handler(self, request):
        """WebSocket 연결 처리"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        agent_id = str(uuid.uuid4())
        logger.info(f"New WebSocket connection: {agent_id}")
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    response = await self.process_method(MCPMessage(**data))
                    await ws.send_json(response)
                except Exception as e:
                    await ws.send_json({"error": str(e)})
                    
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
                
        logger.info(f"WebSocket connection closed: {agent_id}")
        return ws
    
    async def handle_status(self, request: web.Request) -> web.Response:
        """서버 상태 확인"""
        status = {
            "status": "running",
            "agents": len(self.agents),
            "active_tasks": len(self.tasks),
            "timestamp": datetime.now().isoformat()
        }
        return web.json_response(status)
    
    async def handle_list_agents(self, request: web.Request) -> web.Response:
        """연결된 에이전트 목록"""
        return web.json_response({"agents": list(self.agents.values())})
    
    async def send_to_agent(self, agent_id: str, message: dict):
        """에이전트에게 메시지 전송"""
        # WebSocket을 통한 실시간 통신
        logger.info(f"Sending message to agent {agent_id}: {message}")
    
    async def normalize_data(self, data: list) -> list:
        """데이터 정규화"""
        # 실제 정규화 로직 구현
        return data
    
    async def validate_data(self, data: list) -> list:
        """데이터 검증"""
        # 실제 검증 로직 구현
        return data
    
    async def deduplicate_data(self, data: list) -> list:
        """중복 제거"""
        # 실제 중복 제거 로직 구현
        seen = set()
        unique = []
        for item in data:
            key = f"{item.get('platform')}_{item.get('id')}"
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
    
    async def save_to_database(self, data: list) -> dict:
        """데이터베이스 저장"""
        # 실제 DB 저장 로직 구현
        return {"count": len(data), "location": "database"}
    
    async def save_to_file(self, data: list, format: str) -> dict:
        """파일 저장"""
        # 실제 파일 저장 로직 구현
        return {"count": len(data), "location": f"data/export.{format}"}
    
    def run(self):
        """서버 실행"""
        logger.info(f"Starting MCP Server on {self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port)


if __name__ == "__main__":
    server = MCPServer()
    server.run()