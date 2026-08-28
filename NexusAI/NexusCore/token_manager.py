"""
Token Optimizer - Prevents AI models from using excessive tokens
Implements intelligent token budgeting and dynamic allocation
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class TokenStrategy(Enum):
    CONSERVATIVE = "conservative"  # Strict limits, optimal for long-running tasks
    BALANCED = "balanced"          # Moderate limits, good for general use
    AGGRESSIVE = "aggressive"      # Higher limits, for complex reasoning tasks


@dataclass
class TokenBudget:
    """Token budget configuration for an agent"""
    max_tokens: int = 4096
    reserved_tokens: int = 512
    burst_allowance: int = 1024
    current_usage: int = 0
    reset_time: float = 0.0
    
    def reset(self):
        self.current_usage = 0
        self.reset_time = time.time()
    
    def can_spend(self, tokens: int) -> bool:
        available = self.max_tokens - self.current_usage + self.burst_allowance
        return tokens <= available
    
    def spend(self, tokens: int) -> bool:
        if self.can_spend(tokens):
            self.current_usage += tokens
            return True
        return False


@dataclass
class AgentTokenProfile:
    """Token usage profile for monitoring agent behavior"""
    agent_id: str
    total_tokens_used: int = 0
    average_tokens_per_request: float = 0.0
    efficiency_score: float = 1.0  # 0.0 to 1.0, higher is better
    requests_made: int = 0
    throttled_requests: int = 0


class TokenOptimizer:
    """
    Intelligent token management system that prevents excessive token usage
    while maintaining optimal performance across all connected AI agents
    """
    
    def __init__(self, default_strategy: TokenStrategy = TokenStrategy.BALANCED):
        self.strategy = default_strategy
        self.agent_budgets: Dict[str, TokenBudget] = {}
        self.agent_profiles: Dict[str, AgentTokenProfile] = {}
        self.global_token_pool = 100000  # Global token limit for all agents
        self.global_usage = 0
        
        # Strategy-based configurations
        self._configure_strategy()
    
    def _configure_strategy(self):
        """Configure token limits based on selected strategy"""
        if self.strategy == TokenStrategy.CONSERVATIVE:
            self.default_max_tokens = 2048
            self.efficiency_threshold = 0.7
        elif self.strategy == TokenStrategy.BALANCED:
            self.default_max_tokens = 4096
            self.efficiency_threshold = 0.5
        else:  # AGGRESSIVE
            self.default_max_tokens = 8192
            self.efficiency_threshold = 0.3
    
    def register_agent(self, agent_id: str, max_tokens: Optional[int] = None):
        """Register a new agent with token budget"""
        budget = TokenBudget(max_tokens=max_tokens or self.default_max_tokens)
        profile = AgentTokenProfile(agent_id=agent_id)
        
        self.agent_budgets[agent_id] = budget
        self.agent_profiles[agent_id] = profile
    
    def request_tokens(self, agent_id: str, tokens_needed: int, 
                      task_complexity: float = 1.0) -> tuple[bool, int]:
        """
        Request tokens for an agent's operation
        
        Args:
            agent_id: Unique identifier for the agent
            tokens_needed: Number of tokens requested
            task_complexity: Multiplier for task complexity (0.1 to 10.0)
        
        Returns:
            Tuple of (approved: bool, allocated_tokens: int)
        """
        if agent_id not in self.agent_budgets:
            self.register_agent(agent_id)
        
        budget = self.agent_budgets[agent_id]
        profile = self.agent_profiles[agent_id]
        
        # Adjust tokens based on task complexity
        adjusted_tokens = int(tokens_needed * min(max(task_complexity, 0.1), 10.0))
        
        # Check agent-specific budget
        if not budget.can_spend(adjusted_tokens):
            profile.throttled_requests += 1
            # Offer reduced allocation
            reduced_tokens = int(budget.max_tokens * 0.25)
            if budget.can_spend(reduced_tokens):
                return False, reduced_tokens
            return False, 0
        
        # Check global pool
        if self.global_usage + adjusted_tokens > self.global_token_pool:
            return False, 0
        
        # Approve and allocate
        if budget.spend(adjusted_tokens):
            self.global_usage += adjusted_tokens
            profile.total_tokens_used += adjusted_tokens
            profile.requests_made += 1
            
            # Update efficiency metrics
            profile.average_tokens_per_request = (
                profile.total_tokens_used / profile.requests_made
            )
            
            return True, adjusted_tokens
        
        return False, 0
    
    def report_usage(self, agent_id: str, actual_tokens: int, 
                    task_completed: bool = True):
        """Report actual token usage after task completion"""
        if agent_id not in self.agent_profiles:
            return
        
        profile = self.agent_profiles[agent_id]
        
        # Update efficiency score based on completion and usage
        if task_completed:
            expected = profile.average_tokens_per_request
            if expected > 0:
                efficiency = min(actual_tokens / expected, 2.0)
                profile.efficiency_score = (
                    profile.efficiency_score * 0.8 + 
                    (1.0 if efficiency <= 1.0 else 1.0 / efficiency) * 0.2
                )
        else:
            profile.efficiency_score *= 0.9  # Penalty for incomplete tasks
    
    def get_efficiency_report(self, agent_id: str) -> Dict:
        """Get efficiency report for an agent"""
        if agent_id not in self.agent_profiles:
            return {}
        
        profile = self.agent_profiles[agent_id]
        return {
            "agent_id": agent_id,
            "total_tokens": profile.total_tokens_used,
            "average_per_request": profile.average_tokens_per_request,
            "efficiency_score": profile.efficiency_score,
            "throttle_rate": (
                profile.throttled_requests / max(profile.requests_made, 1)
            )
        }
    
    def reset_period(self):
        """Reset all token budgets (called periodically)"""
        for budget in self.agent_budgets.values():
            budget.reset()
        self.global_usage = 0
    
    def optimize_allocation(self, agent_id: str) -> int:
        """
        Dynamically optimize token allocation based on agent's historical performance
        Returns recommended token limit for next period
        """
        if agent_id not in self.agent_profiles:
            return self.default_max_tokens
        
        profile = self.agent_profiles[agent_id]
        current_limit = self.agent_budgets[agent_id].max_tokens
        
        # Increase limit for efficient agents
        if profile.efficiency_score > 0.8:
            return min(current_limit * 1.2, self.default_max_tokens * 2)
        # Decrease limit for inefficient agents
        elif profile.efficiency_score < 0.4:
            return max(current_limit * 0.8, self.default_max_tokens // 2)
        
        return current_limit
