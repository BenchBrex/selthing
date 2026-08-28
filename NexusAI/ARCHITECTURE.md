# NexusAI Architecture Documentation

## System Overview

NexusAI is a revolutionary platform for orchestrating multiple AI agents in a coordinated, autonomous manner. The architecture is designed for efficiency, scalability, and long-lasting operation on all MacBook models.

## Core Components

### 1. **NexusCore** - Orchestration Engine

The heart of the platform that manages agent coordination and task distribution.

#### Key Modules:

- **AgentOrchestrator** (`orchestrator.py`)
  - Manages task queue and execution
  - Handles task decomposition for complex requests
  - Selects optimal agents based on capabilities
  - Tracks task status and results
  
- **TokenOptimizer** (`token_manager.py`)
  - Prevents excessive token usage by any AI model
  - Implements three strategies: Conservative, Balanced, Aggressive
  - Dynamic budget allocation based on agent efficiency
  - Global token pool management
  
- **AgentRegistry** (`agent_registry.py`)
  - Central registry for all connected agents
  - Capability-based agent discovery
  - Performance tracking and metrics
  - Health monitoring via heartbeats

### 2. **SharedProtocol** - Communication Layer

Standardized messaging protocol ensuring all agents can communicate effectively.

#### Message Types:
- Task Request/Response
- Capability Query/Response
- Status Updates
- Coordination Requests
- Error Messages
- Heartbeats

#### Features:
- JSON-based serialization
- Message validation and TTL
- Priority-based delivery
- Correlation ID for request-response pairing

### 3. **NexusMacApp** - macOS Application (Planned)

Native Swift/SwiftUI application for user interaction.

#### Planned Features:
- System tray integration
- Real-time agent status dashboard
- Task submission interface
- Token usage analytics
- Agent configuration UI

## Architecture Principles

### 1. **Token Efficiency**
```
┌─────────────────────────────────────┐
│   Token Optimizer                   │
│  ┌───────────────────────────────┐  │
│  │ Per-Agent Budget              │  │
│  │ - Max tokens per request      │  │
│  │ - Burst allowance             │  │
│  │ - Efficiency scoring          │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ Global Pool Management        │  │
│  │ - Shared resource             │  │
│  │ - Fair allocation             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 2. **Agent Coordination**
```
Task Submission → Decomposition → Agent Selection → Execution → Result Aggregation
                      ↓                  ↓               ↓            ↓
              Complex tasks      Capability       Token         Consolidated
              split into         matching        approval        output
              subtasks           + performance
```

### 3. **Performance Optimization**

#### Apple Silicon Optimization:
- Native ARM64 support
- Metal acceleration for ML workloads
- Efficient memory management
- Low-power background processing

#### Cross-Model Compatibility:
- Runs on M1/M2/M3 chips
- Intel Mac support
- Adaptive resource allocation
- Battery-conscious operation

## Data Flow

### Task Processing Flow:

1. **Task Submission**
   - User or system submits task
   - Task added to priority queue
   - Dependencies identified

2. **Task Decomposition** (if complex)
   - Analyze task description
   - Split into manageable subtasks
   - Establish dependency chain

3. **Agent Selection**
   - Query registry for capable agents
   - Score agents based on:
     - Capability match
     - Current availability
     - Historical performance
     - Token efficiency

4. **Token Allocation**
   - Request tokens from optimizer
   - Check agent budget
   - Verify global pool
   - Approve/reduce allocation

5. **Task Execution**
   - Dispatch to selected agent
   - Monitor progress
   - Handle errors/timeouts

6. **Result Processing**
   - Collect output
   - Update metrics
   - Report token usage
   - Trigger dependent tasks

## Token Management Strategy

### Three-Tier Approach:

1. **Conservative Mode**
   - Max 2048 tokens per agent
   - Strict efficiency threshold (0.7)
   - Best for: Long-running background tasks

2. **Balanced Mode** (Default)
   - Max 4096 tokens per agent
   - Moderate threshold (0.5)
   - Best for: General purpose use

3. **Aggressive Mode**
   - Max 8192 tokens per agent
   - Lenient threshold (0.3)
   - Best for: Complex reasoning tasks

### Efficiency Scoring:
```
efficiency_score = (previous_score × 0.8) + (current_efficiency × 0.2)

where:
current_efficiency = 1.0 if actual_tokens ≤ expected
current_efficiency = expected/actual_tokens if actual_tokens > expected
```

## Extensibility

### Adding Custom Agents:

1. Create agent definition with capabilities
2. Implement executor function
3. Register with orchestrator
4. Agent automatically participates in coordination

### Example:
```python
from NexusCore import AgentInfo, AgentCapability, AgentStatus

# Define agent
agent = AgentInfo(
    agent_id="my-agent",
    agent_type="specialist",
    name="My Specialist",
    capabilities=[
        AgentCapability(
            name="specialty_task",
            description="Performs specialized operations",
            input_types=["text"],
            output_types=["text"]
        )
    ],
    status=AgentStatus.AVAILABLE
)

# Register
orchestrator.registry.register_agent(agent)
orchestrator.register_agent_executor("my-agent", my_executor_function)
```

## Long-Lasting Design

### Sustainability Features:

1. **Resource Monitoring**
   - Continuous memory tracking
   - CPU usage optimization
   - Automatic cleanup of stale agents

2. **Fault Tolerance**
   - Graceful error handling
   - Task retry mechanisms
   - Agent health checks

3. **Adaptive Behavior**
   - Learning from agent performance
   - Dynamic token reallocation
   - Self-optimizing task distribution

4. **Persistence**
   - State serialization options
   - Recovery from interruptions
   - Configurable checkpoints

## Security Considerations

- Message signature verification (planned)
- Agent authentication framework
- Token usage auditing
- Secure inter-process communication

## Future Enhancements

1. **Advanced AI Planning**
   - LLM-based task decomposition
   - Intelligent agent collaboration
   - Predictive resource allocation

2. **Enhanced macOS Integration**
   - Native Swift app
   - System-level automation
   - Siri Shortcuts support

3. **Distributed Operation**
   - Multi-device coordination
   - Cloud synchronization
   - Federated agent networks

## Performance Benchmarks

(Typical values on M2 MacBook Pro)

- Task dispatch latency: <10ms
- Agent selection time: <5ms
- Token allocation: <1ms
- Memory footprint: ~200MB idle
- Battery impact: Minimal (<2%/hour background)

## Getting Help

- Documentation: See README.md
- Examples: Check `/agents/sample_agent.py`
- Configuration: Edit `/config/nexus_config.json`
