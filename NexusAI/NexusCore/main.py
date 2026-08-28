"""
NexusAI Main Entry Point - Starts the orchestration engine
"""

import asyncio
import signal
import sys
from .orchestrator import AgentOrchestrator
from .token_manager import TokenStrategy
from .agent_registry import AgentInfo, AgentCapability, AgentStatus


class NexusAIMain:
    """Main application class for NexusAI platform"""
    
    def __init__(self):
        self.orchestrator = AgentOrchestrator(TokenStrategy.BALANCED)
        self._shutdown = False
    
    def setup_default_agents(self):
        """Register some default agent types for demonstration"""
        
        # Hermes-like general purpose agent
        hermes_agent = AgentInfo(
            agent_id="hermes-general-01",
            agent_type="hermes",
            name="Hermes General Assistant",
            description="General purpose AI assistant based on Hermes architecture",
            capabilities=[
                AgentCapability(
                    name="text_generation",
                    description="Generate human-like text responses",
                    input_types=["text"],
                    output_types=["text"],
                    cost_estimate=1.0
                ),
                AgentCapability(
                    name="reasoning",
                    description="Logical reasoning and problem solving",
                    input_types=["text", "code"],
                    output_types=["text", "code"],
                    cost_estimate=2.0
                ),
                AgentCapability(
                    name="conversation",
                    description="Multi-turn conversation management",
                    input_types=["text"],
                    output_types=["text"],
                    cost_estimate=1.5
                )
            ],
            status=AgentStatus.AVAILABLE
        )
        
        # Code specialist agent
        code_agent = AgentInfo(
            agent_id="code-specialist-01",
            agent_type="code_assistant",
            name="Code Specialist",
            description="Specialized agent for code generation and review",
            capabilities=[
                AgentCapability(
                    name="code_generation",
                    description="Generate code in multiple languages",
                    input_types=["text", "code"],
                    output_types=["code"],
                    cost_estimate=2.5
                ),
                AgentCapability(
                    name="code_review",
                    description="Review and improve existing code",
                    input_types=["code"],
                    output_types=["text", "code"],
                    cost_estimate=2.0
                ),
                AgentCapability(
                    name="debugging",
                    description="Identify and fix bugs in code",
                    input_types=["code", "text"],
                    output_types=["code", "text"],
                    cost_estimate=3.0
                )
            ],
            status=AgentStatus.AVAILABLE
        )
        
        # Research agent
        research_agent = AgentInfo(
            agent_id="research-agent-01",
            agent_type="researcher",
            name="Research Assistant",
            description="Specialized in information gathering and analysis",
            capabilities=[
                AgentCapability(
                    name="information_retrieval",
                    description="Search and retrieve relevant information",
                    input_types=["text"],
                    output_types=["text"],
                    cost_estimate=1.5
                ),
                AgentCapability(
                    name="analysis",
                    description="Analyze and synthesize information",
                    input_types=["text"],
                    output_types=["text"],
                    cost_estimate=2.5
                ),
                AgentCapability(
                    name="summarization",
                    description="Create concise summaries of long content",
                    input_types=["text"],
                    output_types=["text"],
                    cost_estimate=1.0
                )
            ],
            status=AgentStatus.AVAILABLE
        )
        
        # Register agents
        self.orchestrator.registry.register_agent(hermes_agent)
        self.orchestrator.registry.register_agent(code_agent)
        self.orchestrator.registry.register_agent(research_agent)
        
        # Register mock executors for demonstration
        async def mock_executor(input_data, tokens):
            await asyncio.sleep(0.5)  # Simulate processing
            return f"Processed with {tokens} tokens: {str(input_data)[:100]}"
        
        self.orchestrator.register_agent_executor("hermes-general-01", mock_executor)
        self.orchestrator.register_agent_executor("code-specialist-01", mock_executor)
        self.orchestrator.register_agent_executor("research-agent-01", mock_executor)
    
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print("\nShutting down NexusAI...")
        self._shutdown = True
        self.orchestrator.stop()
    
    async def run_demo(self):
        """Run a demonstration of the platform"""
        print("=" * 60)
        print("NexusAI Platform - Autonomous Multi-Agent System")
        print("=" * 60)
        print()
        
        # Setup agents
        self.setup_default_agents()
        print("✓ Registered 3 default agents:")
        print("  - Hermes General Assistant")
        print("  - Code Specialist")
        print("  - Research Assistant")
        print()
        
        # Start orchestrator
        self.orchestrator.start()
        print("✓ Orchestrator started")
        print()
        
        # Submit some demo tasks
        print("Submitting demo tasks...")
        
        task1_id = self.orchestrator.submit_task(
            description="Explain quantum computing basics",
            input_data="quantum computing introduction",
            input_types=["text"],
            priority=7
        )
        print(f"  Task 1 submitted: {task1_id[:8]}...")
        
        task2_id = self.orchestrator.submit_task(
            description="Review this Python code for optimization",
            input_data="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            input_types=["code"],
            priority=5
        )
        print(f"  Task 2 submitted: {task2_id[:8]}...")
        
        task3_id = self.orchestrator.submit_task(
            description="Summarize recent AI research papers",
            input_data="AI research trends 2024",
            input_types=["text"],
            priority=3
        )
        print(f"  Task 3 submitted: {task3_id[:8]}...")
        
        # Wait for tasks to complete
        print()
        print("Processing tasks...")
        await asyncio.sleep(2)
        
        # Show results
        print()
        print("=" * 60)
        print("Results:")
        print("=" * 60)
        
        for task_id in [task1_id, task2_id, task3_id]:
            status = self.orchestrator.get_task_status(task_id)
            if status:
                print(f"\nTask {task_id[:8]}...:")
                print(f"  Status: {status['status']}")
                if status['status'] == 'completed':
                    print(f"  Agent: {status['assigned_agent']}")
                    print(f"  Tokens used: {status['tokens_used']}")
                    print(f"  Execution time: {status['execution_time']:.2f}s")
                elif status['status'] == 'failed':
                    print(f"  Error: {status.get('error', 'Unknown')}")
        
        # Show system metrics
        print()
        print("=" * 60)
        print("System Metrics:")
        print("=" * 60)
        metrics = self.orchestrator.get_system_metrics()
        print(f"  Total agents: {metrics['registered_agents']}")
        print(f"  Available agents: {metrics['available_agents']}")
        print(f"  Tasks completed: {metrics['completed_tasks']}")
        print(f"  Tasks failed: {metrics['failed_tasks']}")
        print(f"  Token usage: {metrics['token_optimizer_stats']['global_usage']}/{metrics['token_optimizer_stats']['global_pool']}")
        
        print()
        print("=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
        self.orchestrator.stop()


def main():
    """Main entry point"""
    app = NexusAIMain()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, app.handle_shutdown)
    signal.signal(signal.SIGTERM, app.handle_shutdown)
    
    try:
        asyncio.run(app.run_demo())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
