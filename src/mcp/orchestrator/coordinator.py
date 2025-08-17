"""
작업 코디네이터 - 작업 분배 및 관리
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import uuid
from enum import Enum
from dataclasses import dataclass
from loguru import logger
import heapq

from ..models.task import Task, TaskStatus, SubTask
from ..models.agent import Agent, AgentStatus, AgentType


class TaskPriority(Enum):
    """작업 우선순위"""
    CRITICAL = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7
    IDLE = 9


class TaskCoordinator:
    """작업 코디네이터"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.subtasks: Dict[str, List[SubTask]] = {}
        self.task_queue: List[tuple] = []  # Priority queue
        self.running_tasks: Dict[str, str] = {}  # task_id -> agent_id
        self.completed_tasks: Dict[str, Any] = {}
        self.task_results: Dict[str, List[Any]] = {}
        self.lock = asyncio.Lock()
        
    async def initialize(self):
        """초기화"""
        logger.info("Initializing Task Coordinator")
        # 백그라운드 작업 시작
        asyncio.create_task(self.task_dispatcher())
        asyncio.create_task(self.result_aggregator())
        
    async def submit_task(self, task: Task) -> str:
        """작업 제출"""
        async with self.lock:
            # 작업 저장
            self.tasks[task.task_id] = task
            
            # 서브태스크 생성
            subtasks = await self.create_subtasks(task)
            self.subtasks[task.task_id] = subtasks
            
            # 우선순위 큐에 추가
            for subtask in subtasks:
                priority = task.priority if hasattr(task, 'priority') else TaskPriority.NORMAL.value
                heapq.heappush(self.task_queue, (priority, subtask.created_at, subtask))
                
            logger.info(f"Task {task.task_id} submitted with {len(subtasks)} subtasks")
            return task.task_id
            
    async def create_subtasks(self, task: Task) -> List[SubTask]:
        """작업을 서브태스크로 분할"""
        subtasks = []
        
        # 플랫폼별, 지역별로 분할
        for platform in task.platforms:
            for area in task.areas:
                subtask = SubTask(
                    subtask_id=f"{task.task_id}_{platform}_{area}",
                    parent_task_id=task.task_id,
                    platform=platform,
                    area=area,
                    filters=task.filters,
                    max_items=task.max_items // (len(task.platforms) * len(task.areas))
                )
                subtasks.append(subtask)
                
        return subtasks
        
    async def task_dispatcher(self):
        """작업 분배 엔진"""
        while True:
            try:
                if self.task_queue:
                    async with self.lock:
                        # 우선순위가 가장 높은 작업 가져오기
                        priority, created_at, subtask = heapq.heappop(self.task_queue)
                        
                        # 적합한 에이전트 찾기
                        agent = await self.find_suitable_agent(subtask)
                        
                        if agent:
                            # 작업 할당
                            await self.assign_task_to_agent(subtask, agent)
                        else:
                            # 에이전트가 없으면 다시 큐에 넣기
                            heapq.heappush(self.task_queue, (priority, created_at, subtask))
                            
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Task dispatcher error: {e}")
                
    async def find_suitable_agent(self, subtask: SubTask) -> Optional[Agent]:
        """적합한 에이전트 찾기"""
        # 실제 구현에서는 AgentRegistry와 연동
        # 여기서는 시뮬레이션
        return None
        
    async def assign_task_to_agent(self, subtask: SubTask, agent: Agent):
        """에이전트에 작업 할당"""
        # 작업 상태 업데이트
        subtask.status = TaskStatus.RUNNING
        subtask.assigned_agent = agent.agent_id
        subtask.started_at = datetime.now()
        
        # 실행 중 작업 추가
        self.running_tasks[subtask.subtask_id] = agent.agent_id
        
        # 에이전트에 메시지 전송
        message = {
            'type': 'task_assignment',
            'subtask_id': subtask.subtask_id,
            'platform': subtask.platform,
            'area': subtask.area,
            'filters': subtask.filters,
            'max_items': subtask.max_items
        }
        
        # 실제로는 메시지 큐나 WebSocket으로 전송
        logger.info(f"Assigned {subtask.subtask_id} to agent {agent.agent_id}")
        
    async def update_task_result(self, subtask_id: str, result: Any):
        """작업 결과 업데이트"""
        async with self.lock:
            # 서브태스크 찾기
            parent_task_id = subtask_id.split('_')[0]
            
            if parent_task_id not in self.task_results:
                self.task_results[parent_task_id] = []
                
            self.task_results[parent_task_id].append(result)
            
            # 실행 중 작업에서 제거
            if subtask_id in self.running_tasks:
                del self.running_tasks[subtask_id]
                
            # 모든 서브태스크가 완료되었는지 확인
            await self.check_task_completion(parent_task_id)
            
    async def check_task_completion(self, task_id: str):
        """작업 완료 확인"""
        if task_id not in self.tasks:
            return
            
        task = self.tasks[task_id]
        subtasks = self.subtasks.get(task_id, [])
        results = self.task_results.get(task_id, [])
        
        if len(results) >= len(subtasks):
            # 모든 서브태스크 완료
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # 결과 집계
            aggregated_result = await self.aggregate_results(results)
            self.completed_tasks[task_id] = aggregated_result
            
            logger.info(f"Task {task_id} completed with {len(results)} results")
            
    async def aggregate_results(self, results: List[Any]) -> dict:
        """결과 집계"""
        total_items = sum(len(r.get('data', [])) for r in results)
        platforms = list(set(r.get('platform') for r in results))
        areas = list(set(r.get('area') for r in results))
        
        return {
            'total_items': total_items,
            'platforms': platforms,
            'areas': areas,
            'results': results,
            'aggregated_at': datetime.now().isoformat()
        }
        
    async def result_aggregator(self):
        """결과 집계 엔진"""
        while True:
            try:
                # 완료된 작업 처리
                for task_id, task in self.tasks.items():
                    if task.status == TaskStatus.COMPLETED and task_id not in self.completed_tasks:
                        results = self.task_results.get(task_id, [])
                        aggregated = await self.aggregate_results(results)
                        self.completed_tasks[task_id] = aggregated
                        
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Result aggregator error: {e}")
                
    async def retry_task(self, task_id: str):
        """작업 재시도"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            
            # 다시 큐에 추가
            await self.submit_task(task)
            logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
            
    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        async with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return False
                
            task.status = TaskStatus.CANCELLED
            
            # 서브태스크 취소
            subtasks = self.subtasks.get(task_id, [])
            for subtask in subtasks:
                subtask.status = TaskStatus.CANCELLED
                
            logger.info(f"Task {task_id} cancelled")
            return True
            
    async def reassign_task(self, subtask_id: str):
        """작업 재할당"""
        # 서브태스크 찾기
        for task_id, subtasks in self.subtasks.items():
            for subtask in subtasks:
                if subtask.subtask_id == subtask_id:
                    # 다시 큐에 추가
                    priority = TaskPriority.HIGH.value  # 재할당은 높은 우선순위
                    heapq.heappush(self.task_queue, (priority, datetime.now(), subtask))
                    logger.info(f"Reassigning subtask {subtask_id}")
                    return
                    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """작업 조회"""
        return self.tasks.get(task_id)
        
    async def get_pending_task_count(self) -> int:
        """대기 중 작업 수"""
        return len(self.task_queue)
        
    async def get_running_task_count(self) -> int:
        """실행 중 작업 수"""
        return len(self.running_tasks)
        
    async def get_completed_task_count(self) -> int:
        """완료된 작업 수"""
        return len(self.completed_tasks)
        
    async def get_average_task_time(self) -> float:
        """평균 작업 시간"""
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        if not completed_tasks:
            return 0
            
        total_time = sum(
            (t.completed_at - t.created_at).total_seconds() 
            for t in completed_tasks 
            if t.completed_at
        )
        return total_time / len(completed_tasks)
        
    async def get_success_rate(self) -> float:
        """성공률"""
        total_tasks = len(self.tasks)
        if total_tasks == 0:
            return 0
            
        successful_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        return (successful_tasks / total_tasks) * 100
        
    def get_status(self) -> dict:
        """코디네이터 상태"""
        return {
            'tasks': {
                'total': len(self.tasks),
                'pending': len(self.task_queue),
                'running': len(self.running_tasks),
                'completed': len(self.completed_tasks)
            },
            'performance': {
                'avg_task_time': asyncio.run(self.get_average_task_time()),
                'success_rate': asyncio.run(self.get_success_rate())
            }
        }