"""
Agent Orchestrator - Coordinates multiple AI agents to work together autonomously
Handles task decomposition, agent selection, and result aggregation
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import uuid

from .agent_registry import AgentRegistry, AgentInfo, AgentStatus, AgentCapability
from .token_manager import TokenOptimizer, TokenStrategy


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task to be executed by an agent"""
    task_id: str
    description: str
    input_data: Any
    input_types: List[str]
    priority: int = 5  # 1-10, higher is more urgent
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    
    def is_ready(self, completed_tasks: set) -> bool:
        """Check if all dependencies are completed"""
        return all(dep in completed_tasks for dep in self.dependencies)


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    success: bool
    output: Any
    agent_id: str
    tokens_used: int
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """
    Main orchestrator that coordinates multiple AI agents to work together
    Implements intelligent task distribution and autonomous coordination
    """
    
    def __init__(self, token_strategy: TokenStrategy = TokenStrategy.BALANCED):
        self.registry = AgentRegistry()
        self.token_optimizer = TokenOptimizer(token_strategy)
        
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        
        self.agent_executors: Dict[str, Callable] = {}  # agent_id -> execution function
        self._running = False
        self._orchestration_task = None
    
    def register_agent_executor(self, agent_id: str, executor: Callable):
        """Register an execution function for an agent"""
        self.agent_executors[agent_id] = executor
        self.token_optimizer.register_agent(agent_id)
    
    def submit_task(self, description: str, input_data: Any, 
                   input_types: List[str], priority: int = 5,
                   dependencies: List[str] = None) -> str:
        """Submit a new task to the orchestrator"""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            description=description,
            input_data=input_data,
            input_types=input_types,
            priority=priority,
            dependencies=dependencies or []
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        return task_id
    
    def submit_complex_task(self, description: str, input_data: Any,
                           input_types: List[str]) -> List[str]:
        """
        Submit a complex task that will be automatically decomposed
        Returns list of sub-task IDs
        """
        # Simple decomposition strategy (can be enhanced with AI)
        subtasks = self._decompose_task(description, input_data, input_types)
        task_ids = []
        
        prev_task_id = None
        for i, subtask in enumerate(subtasks):
            deps = [prev_task_id] if prev_task_id else []
            task_id = self.submit_task(
                description=subtask["description"],
                input_data=subtask.get("input_data", input_data),
                input_types=subtask.get("input_types", input_types),
                priority=subtask.get("priority", 5),
                dependencies=deps
            )
            task_ids.append(task_id)
            prev_task_id = task_id
        
        return task_ids
    
    def _decompose_task(self, description: str, input_data: Any,
                       input_types: List[str]) -> List[Dict]:
        """
        Decompose a complex task into simpler subtasks
        This is a basic implementation - can be enhanced with AI planning
        """
        # Basic decomposition heuristics
        subtasks = []
        
        # Check if task involves multiple steps
        if "and" in description.lower():
            parts = description.split(" and ")
            for i, part in enumerate(parts):
                subtasks.append({
                    "description": part.strip(),
                    "priority": 5 - i  # Earlier tasks have higher priority
                })
        elif "then" in description.lower():
            parts = description.split(" then ")
            for i, part in enumerate(parts):
                subtasks.append({
                    "description": part.strip(),
                    "priority": 5 - i
                })
        else:
            # Single task
            subtasks.append({
                "description": description,
                "priority": 5
            })
        
        return subtasks
    
    async def select_best_agent(self, task: Task) -> Optional[AgentInfo]:
        """Select the best available agent for a task"""
        # Find agents with required capabilities
        best_agent = self.registry.find_best_agent(
            task.description,
            task.input_types
        )
        
        if best_agent:
            return best_agent
        
        # Fallback: find any available agent
        available = self.registry.get_all_agents(AgentStatus.AVAILABLE)
        if available:
            return available[0]
        
        return None
    
    async def execute_task(self, task: Task, agent: AgentInfo) -> TaskResult:
        """Execute a task using the selected agent"""
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_agent = agent.agent_id
        task.started_at = time.time()
        
        start_time = time.time()
        tokens_requested = 1024  # Default estimate
        
        try:
            # Request tokens from optimizer
            complexity = task.priority / 5.0  # Higher priority = more complex
            approved, allocated_tokens = self.token_optimizer.request_tokens(
                agent.agent_id,
                tokens_requested,
                complexity
            )
            
            if not approved and allocated_tokens == 0:
                raise Exception("Token budget exceeded")
            
            # Get executor for this agent
            executor = self.agent_executors.get(agent.agent_id)
            if not executor:
                raise Exception(f"No executor registered for agent {agent.agent_id}")
            
            # Execute the task
            if asyncio.iscoroutinefunction(executor):
                result = await executor(task.input_data, allocated_tokens)
            else:
                result = executor(task.input_data, allocated_tokens)
            
            execution_time = time.time() - start_time
            actual_tokens = allocated_tokens  # Could be refined based on actual usage
            
            # Report token usage
            self.token_optimizer.report_usage(
                agent.agent_id,
                actual_tokens,
                task_completed=True
            )
            
            # Update agent metrics
            self.registry.update_agent_metrics(
                agent.agent_id,
                execution_time,
                success=True
            )
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                output=result,
                agent_id=agent.agent_id,
                tokens_used=actual_tokens,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.token_optimizer.report_usage(
                agent.agent_id,
                0,
                task_completed=False
            )
            
            self.registry.update_agent_metrics(
                agent.agent_id,
                execution_time,
                success=False
            )
            
            return TaskResult(
                task_id=task.task_id,
                success=False,
                output=None,
                agent_id=agent.agent_id,
                tokens_used=0,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )
    
    async def orchestration_loop(self):
        """Main orchestration loop that processes tasks"""
        self._running = True
        
        while self._running:
            # Process ready tasks
            ready_tasks = []
            for task in self.task_queue:
                if task.status == TaskStatus.PENDING and task.is_ready(set(self.completed_tasks.keys())):
                    ready_tasks.append(task)
            
            # Execute ready tasks concurrently
            if ready_tasks:
                execution_tasks = []
                for task in ready_tasks:
                    agent = await self.select_best_agent(task)
                    if agent:
                        task.status = TaskStatus.IN_PROGRESS
                        self.active_tasks[task.task_id] = task
                        execution_tasks.append(self.execute_task(task, agent))
                
                if execution_tasks:
                    results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, TaskResult):
                            if result.success:
                                self.completed_tasks[result.task_id] = result
                                if result.task_id in self.active_tasks:
                                    self.active_tasks[result.task_id].status = TaskStatus.COMPLETED
                                    self.active_tasks[result.task_id].completed_at = time.time()
                            else:
                                self.failed_tasks[result.task_id] = result
                                if result.task_id in self.active_tasks:
                                    self.active_tasks[result.task_id].status = TaskStatus.FAILED
                                    self.active_tasks[result.task_id].error = result.metadata.get("error", "Unknown error")
                            
                            # Remove from queue and active tasks
                            self.task_queue = [t for t in self.task_queue if t.task_id != result.task_id]
                            self.active_tasks.pop(result.task_id, None)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    def start(self):
        """Start the orchestration loop"""
        if not self._running:
            self._running = True
            self._orchestration_task = asyncio.create_task(self.orchestration_loop())
    
    def stop(self):
        """Stop the orchestration loop"""
        self._running = False
        if self._orchestration_task:
            self._orchestration_task.cancel()
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        for task in self.task_queue:
            if task.task_id == task_id:
                return {
                    "task_id": task_id,
                    "status": task.status.value,
                    "assigned_agent": task.assigned_agent,
                    "progress": "pending"
                }
        
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "completed",
                "assigned_agent": result.agent_id,
                "tokens_used": result.tokens_used,
                "execution_time": result.execution_time
            }
        
        if task_id in self.failed_tasks:
            result = self.failed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "failed",
                "assigned_agent": result.agent_id,
                "error": result.metadata.get("error", "Unknown error")
            }
        
        return None
    
    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
        return {
            "queue_size": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "registered_agents": len(self.registry.agents),
            "available_agents": len([a for a in self.registry.agents.values() if a.is_available()]),
            "token_optimizer_stats": {
                "global_usage": self.token_optimizer.global_usage,
                "global_pool": self.token_optimizer.global_token_pool
            },
            "registry_status": self.registry.get_system_status()
        }
