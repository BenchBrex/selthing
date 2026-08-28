"""
Agent Registry - Manages registration, discovery, and capability tracking of AI agents
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
import time


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class AgentCapability:
    """Represents a specific capability of an agent"""
    
    def __init__(self, name: str, description: str, 
                 input_types: List[str], output_types: List[str],
                 cost_estimate: float = 1.0):
        self.name = name
        self.description = description
        self.input_types = input_types  # e.g., ["text", "image"]
        self.output_types = output_types  # e.g., ["text", "code"]
        self.cost_estimate = cost_estimate  # Relative computational cost
        self.usage_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_types": self.input_types,
            "output_types": self.output_types,
            "cost_estimate": self.cost_estimate,
            "usage_count": self.usage_count
        }


@dataclass
class AgentInfo:
    """Complete information about a registered agent"""
    agent_id: str
    agent_type: str  # e.g., "hermes", "code_assistant", "researcher"
    name: str
    description: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    status: AgentStatus = AgentStatus.OFFLINE
    last_seen: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    total_tasks_completed: int = 0
    average_response_time: float = 0.0
    success_rate: float = 1.0
    
    def is_available(self) -> bool:
        return self.status == AgentStatus.AVAILABLE
    
    def can_handle(self, task_type: str) -> bool:
        """Check if agent has capability for given task type"""
        return any(cap.name == task_type or task_type in cap.input_types 
                  for cap in self.capabilities)
    
    def update_status(self, status: AgentStatus):
        self.status = status
        self.last_seen = time.time()


class AgentRegistry:
    """
    Central registry for all AI agents in the NexusAI platform
    Handles agent discovery, capability matching, and coordination
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.capability_index: Dict[str, Set[str]] = {}  # capability -> agent_ids
        self.agent_types: Dict[str, Set[str]] = {}  # type -> agent_ids
        self._lock = False  # Simple lock for thread safety
    
    def register_agent(self, agent_info: AgentInfo) -> bool:
        """Register a new agent with the system"""
        if self._lock:
            return False
        
        try:
            self._lock = True
            
            if agent_info.agent_id in self.agents:
                # Update existing agent
                self.agents[agent_info.agent_id] = agent_info
            else:
                # New registration
                self.agents[agent_info.agent_id] = agent_info
                
                # Index by type
                if agent_info.agent_type not in self.agent_types:
                    self.agent_types[agent_info.agent_type] = set()
                self.agent_types[agent_info.agent_type].add(agent_info.agent_id)
                
                # Index by capabilities
                for capability in agent_info.capabilities:
                    if capability.name not in self.capability_index:
                        self.capability_index[capability.name] = set()
                    self.capability_index[capability.name].add(agent_info.agent_id)
                    
                    # Also index by input/output types
                    for input_type in capability.input_types:
                        key = f"input:{input_type}"
                        if key not in self.capability_index:
                            self.capability_index[key] = set()
                        self.capability_index[key].add(agent_info.agent_id)
            
            return True
        finally:
            self._lock = False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Remove from indexes
        if agent.agent_type in self.agent_types:
            self.agent_types[agent.agent_type].discard(agent_id)
        
        for capability in agent.capabilities:
            if capability.name in self.capability_index:
                self.capability_index[capability.name].discard(agent_id)
        
        del self.agents[agent_id]
        return True
    
    def find_agents_by_capability(self, capability_name: str, 
                                  required: bool = True) -> List[AgentInfo]:
        """Find all agents that have a specific capability"""
        agent_ids = self.capability_index.get(capability_name, set())
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        
        if required:
            # Filter to only available agents
            return [a for a in agents if a.is_available()]
        return agents
    
    def find_agents_by_input_type(self, input_type: str) -> List[AgentInfo]:
        """Find agents that can process a specific input type"""
        key = f"input:{input_type}"
        return self.find_agents_by_capability(key, required=False)
    
    def find_best_agent(self, task_description: str, 
                       input_data_types: List[str]) -> Optional[AgentInfo]:
        """
        Find the best agent for a given task using capability matching
        Returns the most suitable available agent
        """
        candidate_scores: Dict[str, float] = {}
        
        for agent_id, agent in self.agents.items():
            if not agent.is_available():
                continue
            
            score = 0.0
            
            # Check input type compatibility
            for input_type in input_data_types:
                if agent.can_handle(input_type):
                    score += 2.0
            
            # Check capability match (simple keyword matching)
            task_keywords = task_description.lower().split()
            for capability in agent.capabilities:
                if any(keyword in capability.name.lower() or 
                      keyword in capability.description.lower() 
                      for keyword in task_keywords):
                    score += 3.0
            
            # Prefer agents with better performance metrics
            score *= agent.success_rate
            
            # Prefer faster agents
            if agent.average_response_time > 0:
                score *= (1.0 / max(agent.average_response_time, 0.1))
            
            candidate_scores[agent_id] = score
        
        if not candidate_scores:
            return None
        
        best_agent_id = max(candidate_scores, key=candidate_scores.get)
        return self.agents[best_agent_id]
    
    def get_all_agents(self, status_filter: Optional[AgentStatus] = None) -> List[AgentInfo]:
        """Get all registered agents, optionally filtered by status"""
        if status_filter is None:
            return list(self.agents.values())
        return [a for a in self.agents.values() if a.status == status_filter]
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get specific agent by ID"""
        return self.agents.get(agent_id)
    
    def update_agent_metrics(self, agent_id: str, 
                            response_time: float, 
                            success: bool):
        """Update performance metrics for an agent"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        agent.total_tasks_completed += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.3
        agent.average_response_time = (
            alpha * response_time + 
            (1 - alpha) * agent.average_response_time
        )
        
        # Update success rate
        if success:
            agent.success_rate = min(1.0, agent.success_rate * 1.02)
        else:
            agent.success_rate = max(0.0, agent.success_rate * 0.95)
    
    def get_system_status(self) -> Dict:
        """Get overall system status and statistics"""
        total_agents = len(self.agents)
        available = sum(1 for a in self.agents.values() if a.is_available())
        busy = sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)
        offline = sum(1 for a in self.agents.values() if a.status == AgentStatus.OFFLINE)
        
        return {
            "total_agents": total_agents,
            "available": available,
            "busy": busy,
            "offline": offline,
            "agent_types": list(self.agent_types.keys()),
            "capabilities_registered": len(self.capability_index),
            "timestamp": time.time()
        }
    
    def heartbeat(self, agent_id: str):
        """Update last seen timestamp for an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].last_seen = time.time()
    
    def check_stale_agents(self, timeout_seconds: float = 300.0) -> List[str]:
        """Find agents that haven't sent heartbeat within timeout"""
        current_time = time.time()
        stale_agents = []
        
        for agent_id, agent in self.agents.items():
            if agent.status != AgentStatus.OFFLINE:
                if current_time - agent.last_seen > timeout_seconds:
                    stale_agents.append(agent_id)
                    agent.status = AgentStatus.OFFLINE
        
        return stale_agents
