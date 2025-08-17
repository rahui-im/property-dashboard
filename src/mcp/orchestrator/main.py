"""
MCP 오케스트레이터 메인 서버 - 실제 구현
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
import asyncio
import uvicorn
from datetime import datetime
import json
import uuid
from loguru import logger
from contextlib import asynccontextmanager

from .coordinator import TaskCoordinator
from .scheduler import TaskScheduler
from .monitor import SystemMonitor
from .registry import AgentRegistry
from ..communication.websocket_manager import WebSocketManager
from ..communication.message_queue import MessageQueue
from ..models.task import Task, TaskStatus
from ..models.agent import Agent, AgentType, AgentStatus

# 로거 설정
logger.add("logs/orchestrator_{time}.log", rotation="1 day", level="INFO")


class MCPOrchestrator:
    """MCP 오케스트레이터 메인 클래스"""
    
    def __init__(self):
        self.coordinator = TaskCoordinator()
        self.scheduler = TaskScheduler()
        self.monitor = SystemMonitor()
        self.registry = AgentRegistry()
        self.ws_manager = WebSocketManager()
        self.message_queue = MessageQueue()
        self.is_running = False
        
    async def start(self):
        """오케스트레이터 시작"""
        try:
            logger.info("Starting MCP Orchestrator...")
            
            # 컴포넌트 초기화
            await self.message_queue.connect()
            await self.coordinator.initialize()
            await self.scheduler.start()
            await self.monitor.start()
            
            self.is_running = True
            
            # 백그라운드 태스크 시작
            asyncio.create_task(self.process_messages())
            asyncio.create_task(self.health_check_loop())
            asyncio.create_task(self.metrics_collection_loop())
            
            logger.info("MCP Orchestrator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start orchestrator: {e}")
            raise
            
    async def stop(self):
        """오케스트레이터 중지"""
        logger.info("Stopping MCP Orchestrator...")
        self.is_running = False
        
        await self.scheduler.stop()
        await self.monitor.stop()
        await self.message_queue.disconnect()
        await self.ws_manager.disconnect_all()
        
        logger.info("MCP Orchestrator stopped")
        
    async def process_messages(self):
        """메시지 큐 처리"""
        while self.is_running:
            try:
                message = await self.message_queue.get_message(timeout=1)
                if message:
                    await self.handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                
    async def handle_message(self, message: dict):
        """메시지 처리"""
        msg_type = message.get('type')
        
        if msg_type == 'task_result':
            await self.handle_task_result(message)
        elif msg_type == 'agent_status':
            await self.handle_agent_status(message)
        elif msg_type == 'error':
            await self.handle_error(message)
            
    async def handle_task_result(self, message: dict):
        """작업 결과 처리"""
        task_id = message.get('task_id')
        result = message.get('result')
        agent_id = message.get('agent_id')
        
        # 결과 저장
        await self.coordinator.update_task_result(task_id, result)
        
        # 에이전트 상태 업데이트
        await self.registry.update_agent_status(agent_id, AgentStatus.IDLE)
        
        # 웹소켓으로 클라이언트에 알림
        await self.ws_manager.broadcast({
            'type': 'task_completed',
            'task_id': task_id,
            'result_summary': {
                'items_collected': len(result.get('data', [])),
                'platform': result.get('platform'),
                'area': result.get('area')
            }
        })
        
    async def handle_agent_status(self, message: dict):
        """에이전트 상태 업데이트"""
        agent_id = message.get('agent_id')
        status = message.get('status')
        
        await self.registry.update_agent_status(agent_id, status)
        
    async def handle_error(self, message: dict):
        """에러 처리"""
        error_type = message.get('error_type')
        error_message = message.get('error_message')
        context = message.get('context', {})
        
        logger.error(f"Error from agent: {error_type} - {error_message}")
        
        # 에러 복구 시도
        if error_type == 'task_failure':
            task_id = context.get('task_id')
            if task_id:
                await self.coordinator.retry_task(task_id)
                
    async def health_check_loop(self):
        """에이전트 헬스체크"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # 30초마다 체크
                
                agents = await self.registry.get_all_agents()
                for agent in agents:
                    if not await self.check_agent_health(agent):
                        await self.handle_unhealthy_agent(agent)
                        
            except Exception as e:
                logger.error(f"Health check error: {e}")
                
    async def check_agent_health(self, agent: Agent) -> bool:
        """에이전트 헬스 체크"""
        # 마지막 하트비트 확인
        last_heartbeat = agent.last_heartbeat
        if not last_heartbeat:
            return False
            
        time_diff = (datetime.now() - last_heartbeat).total_seconds()
        return time_diff < 60  # 60초 이내
        
    async def handle_unhealthy_agent(self, agent: Agent):
        """비정상 에이전트 처리"""
        logger.warning(f"Agent {agent.agent_id} is unhealthy")
        
        # 에이전트 상태를 오프라인으로 변경
        await self.registry.update_agent_status(agent.agent_id, AgentStatus.OFFLINE)
        
        # 진행 중인 작업 재할당
        if agent.current_task:
            await self.coordinator.reassign_task(agent.current_task)
            
    async def metrics_collection_loop(self):
        """메트릭 수집"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # 10초마다 수집
                
                metrics = await self.collect_metrics()
                await self.monitor.record_metrics(metrics)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                
    async def collect_metrics(self) -> dict:
        """시스템 메트릭 수집"""
        return {
            'timestamp': datetime.now().isoformat(),
            'agents': {
                'total': await self.registry.get_agent_count(),
                'active': await self.registry.get_active_agent_count(),
                'idle': await self.registry.get_idle_agent_count()
            },
            'tasks': {
                'pending': await self.coordinator.get_pending_task_count(),
                'running': await self.coordinator.get_running_task_count(),
                'completed': await self.coordinator.get_completed_task_count()
            },
            'performance': {
                'avg_task_time': await self.coordinator.get_average_task_time(),
                'success_rate': await self.coordinator.get_success_rate()
            }
        }


# FastAPI 앱 인스턴스
orchestrator = MCPOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # 시작
    await orchestrator.start()
    yield
    # 종료
    await orchestrator.stop()

app = FastAPI(
    title="MCP Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API 엔드포인트

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "MCP Orchestrator",
        "version": "1.0.0",
        "status": "running" if orchestrator.is_running else "stopped"
    }


@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "coordinator": "running",
            "scheduler": "running",
            "monitor": "running",
            "message_queue": "connected"
        }
    }


@app.post("/api/v1/tasks")
async def create_task(task_data: dict):
    """새 작업 생성"""
    try:
        task = Task(
            task_id=str(uuid.uuid4()),
            type=task_data.get('type', 'collect'),
            areas=task_data.get('areas', []),
            platforms=task_data.get('platforms', []),
            filters=task_data.get('filters', {}),
            priority=task_data.get('priority', 5),
            status=TaskStatus.PENDING
        )
        
        # 작업 스케줄링
        await orchestrator.coordinator.submit_task(task)
        
        return {
            "task_id": task.task_id,
            "status": "submitted",
            "estimated_time": task.estimate_completion_time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    task = await orchestrator.coordinator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "result": task.result if task.status == TaskStatus.COMPLETED else None
    }


@app.delete("/api/v1/tasks/{task_id}")
async def cancel_task(task_id: str):
    """작업 취소"""
    success = await orchestrator.coordinator.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
        
    return {"status": "cancelled"}


@app.get("/api/v1/agents")
async def list_agents():
    """에이전트 목록 조회"""
    agents = await orchestrator.registry.get_all_agents()
    return {
        "agents": [
            {
                "agent_id": agent.agent_id,
                "type": agent.type.value,
                "status": agent.status.value,
                "platform": agent.platform,
                "current_task": agent.current_task,
                "performance_score": agent.performance_score
            }
            for agent in agents
        ]
    }


@app.post("/api/v1/agents/register")
async def register_agent(agent_data: dict):
    """에이전트 등록"""
    agent = Agent(
        agent_id=str(uuid.uuid4()),
        type=AgentType(agent_data.get('type')),
        platform=agent_data.get('platform'),
        capabilities=agent_data.get('capabilities', []),
        status=AgentStatus.IDLE
    )
    
    success = await orchestrator.registry.register_agent(agent)
    if not success:
        raise HTTPException(status_code=400, detail="Agent registration failed")
        
    return {
        "agent_id": agent.agent_id,
        "status": "registered"
    }


@app.get("/api/v1/metrics")
async def get_metrics():
    """시스템 메트릭 조회"""
    metrics = await orchestrator.collect_metrics()
    return metrics


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 연결"""
    await orchestrator.ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 메시지 처리
            if message.get('type') == 'subscribe':
                await orchestrator.ws_manager.subscribe(client_id, message.get('channel'))
            elif message.get('type') == 'unsubscribe':
                await orchestrator.ws_manager.unsubscribe(client_id, message.get('channel'))
                
    except WebSocketDisconnect:
        await orchestrator.ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await orchestrator.ws_manager.disconnect(client_id)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )