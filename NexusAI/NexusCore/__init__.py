"""
NexusCore - Main orchestration engine for autonomous AI agent coordination
"""

from .orchestrator import AgentOrchestrator
from .token_manager import TokenOptimizer
from .agent_registry import AgentRegistry

__version__ = "1.0.0"
__all__ = ["AgentOrchestrator", "TokenOptimizer", "AgentRegistry"]
