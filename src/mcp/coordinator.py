"""
매물 수집 코디네이터 - 서브에이전트 오케스트레이션
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import uuid
from loguru import logger
import json


class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CollectionTask:
    """수집 작업 정의"""
    task_id: str
    areas: List[str]
    platforms: List[str]
    property_types: List[str]
    trade_types: List[str]
    max_items: int
    priority: int = 5
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()


@dataclass
class SubAgent:
    """서브에이전트 정보"""
    agent_id: str
    agent_type: str  # collector, processor, storage
    platform: Optional[str]  # 수집기의 경우 플랫폼
    status: AgentStatus
    capabilities: List[str]
    current_task: Optional[str] = None
    performance_score: float = 1.0
    last_heartbeat: datetime = None
    
    def __post_init__(self):
        if not self.last_heartbeat:
            self.last_heartbeat = datetime.now()


class CollectionCoordinator:
    """매물 수집 코디네이터"""
    
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.tasks: Dict[str, CollectionTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[str, List[Dict]] = {}
        self.running = False
        
    async def start(self):
        """코디네이터 시작"""
        self.running = True
        logger.info("Collection Coordinator started")
        
        # 백그라운드 작업 시작
        asyncio.create_task(self.task_dispatcher())
        asyncio.create_task(self.health_monitor())
        asyncio.create_task(self.result_aggregator())
        
    async def stop(self):
        """코디네이터 중지"""
        self.running = False
        logger.info("Collection Coordinator stopped")
        
    def register_agent(self, agent: SubAgent) -> bool:
        """서브에이전트 등록"""
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered")
            return False
            
        self.agents[agent.agent_id] = agent
        logger.info(f"Agent {agent.agent_id} registered: {agent.agent_type} - {agent.platform}")
        return True
        
    def unregister_agent(self, agent_id: str) -> bool:
        """서브에이전트 등록 해제"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")
            return True
        return False
        
    async def submit_task(self, task: CollectionTask) -> str:
        """수집 작업 제출"""
        self.tasks[task.task_id] = task
        await self.task_queue.put(task)
        logger.info(f"Task {task.task_id} submitted: {len(task.areas)} areas, {len(task.platforms)} platforms")
        return task.task_id
        
    async def task_dispatcher(self):
        """작업 분배 엔진"""
        while self.running:
            try:
                # 큐에서 작업 가져오기
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # 작업을 서브태스크로 분할
                subtasks = self.split_task(task)
                
                # 각 서브태스크를 적절한 에이전트에 할당
                for subtask in subtasks:
                    agent = self.find_best_agent(subtask)
                    if agent:
                        await self.assign_task_to_agent(subtask, agent)
                    else:
                        # 사용 가능한 에이전트가 없으면 다시 큐에 넣기
                        await self.task_queue.put(subtask)
                        await asyncio.sleep(5)
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task dispatcher error: {e}")
                
    def split_task(self, task: CollectionTask) -> List[Dict]:
        """작업을 서브태스크로 분할"""
        subtasks = []
        
        # 플랫폼별, 지역별로 분할
        for platform in task.platforms:
            for area in task.areas:
                subtask = {
                    'parent_task_id': task.task_id,
                    'subtask_id': f"{task.task_id}_{platform}_{area}",
                    'platform': platform,
                    'area': area,
                    'property_types': task.property_types,
                    'trade_types': task.trade_types,
                    'max_items': task.max_items // (len(task.platforms) * len(task.areas)),
                    'priority': task.priority
                }
                subtasks.append(subtask)
                
        return subtasks
        
    def find_best_agent(self, subtask: Dict) -> Optional[SubAgent]:
        """서브태스크에 가장 적합한 에이전트 찾기"""
        platform = subtask['platform']
        
        # 해당 플랫폼을 처리할 수 있는 유휴 에이전트 찾기
        candidates = [
            agent for agent in self.agents.values()
            if agent.agent_type == 'collector'
            and agent.platform == platform
            and agent.status == AgentStatus.IDLE
        ]
        
        if not candidates:
            return None
            
        # 성능 점수가 가장 높은 에이전트 선택
        best_agent = max(candidates, key=lambda a: a.performance_score)
        return best_agent
        
    async def assign_task_to_agent(self, subtask: Dict, agent: SubAgent):
        """에이전트에 작업 할당"""
        agent.status = AgentStatus.BUSY
        agent.current_task = subtask['subtask_id']
        
        # 에이전트에게 작업 전송 (실제로는 WebSocket이나 메시지 큐 사용)
        message = {
            'type': 'task_assignment',
            'agent_id': agent.agent_id,
            'task': subtask
        }
        
        logger.info(f"Assigned {subtask['subtask_id']} to agent {agent.agent_id}")
        
        # 작업 완료 대기 (시뮬레이션)
        asyncio.create_task(self.simulate_agent_work(agent, subtask))
        
    async def simulate_agent_work(self, agent: SubAgent, subtask: Dict):
        """에이전트 작업 시뮬레이션 (실제로는 에이전트가 직접 처리)"""
        import random
        
        # 작업 시간 시뮬레이션
        work_time = random.uniform(5, 20)
        await asyncio.sleep(work_time)
        
        # 결과 생성 (시뮬레이션)
        result = {
            'subtask_id': subtask['subtask_id'],
            'agent_id': agent.agent_id,
            'platform': subtask['platform'],
            'area': subtask['area'],
            'collected_count': random.randint(10, 50),
            'data': [],  # 실제 수집된 데이터
            'completed_at': datetime.now().isoformat()
        }
        
        # 결과 저장
        parent_task_id = subtask['parent_task_id']
        if parent_task_id not in self.results:
            self.results[parent_task_id] = []
        self.results[parent_task_id].append(result)
        
        # 에이전트 상태 업데이트
        agent.status = AgentStatus.IDLE
        agent.current_task = None
        agent.performance_score = min(1.0, agent.performance_score + 0.01)
        
        logger.info(f"Agent {agent.agent_id} completed {subtask['subtask_id']}")
        
    async def health_monitor(self):
        """에이전트 상태 모니터링"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for agent in self.agents.values():
                    # 하트비트 체크 (30초 이상 응답 없으면 오프라인)
                    time_diff = (current_time - agent.last_heartbeat).total_seconds()
                    
                    if time_diff > 30 and agent.status != AgentStatus.OFFLINE:
                        logger.warning(f"Agent {agent.agent_id} is offline")
                        agent.status = AgentStatus.OFFLINE
                        
                        # 진행 중인 작업 재할당
                        if agent.current_task:
                            await self.reassign_task(agent.current_task)
                            
                await asyncio.sleep(10)  # 10초마다 체크
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                
    async def reassign_task(self, task_id: str):
        """작업 재할당"""
        logger.info(f"Reassigning task {task_id}")
        # 작업을 다시 큐에 넣기
        # 실제 구현에서는 작업 정보를 복원해야 함
        
    async def result_aggregator(self):
        """결과 집계"""
        while self.running:
            try:
                # 완료된 작업 확인
                for task_id, task in self.tasks.items():
                    if task_id in self.results:
                        results = self.results[task_id]
                        
                        # 모든 서브태스크가 완료되었는지 확인
                        expected_count = len(task.platforms) * len(task.areas)
                        if len(results) >= expected_count:
                            # 결과 집계
                            total_collected = sum(r['collected_count'] for r in results)
                            logger.info(f"Task {task_id} completed: {total_collected} items collected")
                            
                            # 데이터 처리 에이전트로 전송
                            await self.send_to_processors(task_id, results)
                            
                await asyncio.sleep(5)  # 5초마다 체크
                
            except Exception as e:
                logger.error(f"Result aggregator error: {e}")
                
    async def send_to_processors(self, task_id: str, results: List[Dict]):
        """데이터 처리 에이전트로 전송"""
        # 정규화 에이전트 찾기
        normalizer = next(
            (agent for agent in self.agents.values() 
             if agent.agent_type == 'normalizer' and agent.status == AgentStatus.IDLE),
            None
        )
        
        if normalizer:
            logger.info(f"Sending {task_id} results to normalizer {normalizer.agent_id}")
            # 실제로는 메시지 전송
        else:
            logger.warning("No available normalizer agent")
            
    def get_status(self) -> Dict:
        """코디네이터 상태 반환"""
        return {
            'running': self.running,
            'agents': {
                'total': len(self.agents),
                'idle': len([a for a in self.agents.values() if a.status == AgentStatus.IDLE]),
                'busy': len([a for a in self.agents.values() if a.status == AgentStatus.BUSY]),
                'offline': len([a for a in self.agents.values() if a.status == AgentStatus.OFFLINE])
            },
            'tasks': {
                'total': len(self.tasks),
                'queued': self.task_queue.qsize(),
                'completed': len([t for t, r in self.results.items() if t in self.tasks])
            },
            'timestamp': datetime.now().isoformat()
        }
        
    def get_agent_performance(self) -> List[Dict]:
        """에이전트 성능 통계"""
        stats = []
        for agent in self.agents.values():
            stats.append({
                'agent_id': agent.agent_id,
                'type': agent.agent_type,
                'platform': agent.platform,
                'status': agent.status.value,
                'performance_score': agent.performance_score,
                'current_task': agent.current_task
            })
        return stats


# 코디네이터 인스턴스 (싱글톤)
coordinator = CollectionCoordinator()


async def main():
    """테스트용 메인 함수"""
    # 코디네이터 시작
    await coordinator.start()
    
    # 테스트 에이전트 등록
    for platform in ['naver', 'zigbang', 'dabang']:
        for i in range(2):  # 각 플랫폼당 2개 에이전트
            agent = SubAgent(
                agent_id=f"{platform}_collector_{i}",
                agent_type='collector',
                platform=platform,
                status=AgentStatus.IDLE,
                capabilities=['apartment', 'officetel']
            )
            coordinator.register_agent(agent)
    
    # 테스트 작업 제출
    task = CollectionTask(
        task_id='test_task_001',
        areas=['강남구', '서초구'],
        platforms=['naver', 'zigbang', 'dabang'],
        property_types=['apartment'],
        trade_types=['sales'],
        max_items=100
    )
    
    await coordinator.submit_task(task)
    
    # 상태 모니터링
    for _ in range(10):
        await asyncio.sleep(5)
        status = coordinator.get_status()
        logger.info(f"Coordinator status: {status}")
        
    await coordinator.stop()


if __name__ == "__main__":
    asyncio.run(main())