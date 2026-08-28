#!/bin/bash

# NexusAI Setup Script for macOS
# This script sets up the development environment for NexusAI platform

set -e

echo "=============================================="
echo "NexusAI Platform - Setup Script"
echo "=============================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ Detected macOS system"
else
    echo "⚠ Warning: This script is optimized for macOS"
    echo "  Continuing with generic setup..."
fi

# Check Python version
echo ""
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found $PYTHON_VERSION"
else
    echo "✗ Python 3.11+ is required"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✓ Virtual environment created and activated"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install asyncio dataclasses-json

# Check for Xcode Command Line Tools (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "Checking Xcode Command Line Tools..."
    if xcode-select --version &> /dev/null; then
        echo "✓ Xcode Command Line Tools installed"
    else
        echo "⚠ Xcode Command Line Tools not found"
        echo "  Install with: xcode-select --install"
    fi
fi

# Create necessary directories
echo ""
echo "Creating project structure..."
mkdir -p logs
mkdir -p agents
mkdir -p config
echo "✓ Project structure created"

# Generate default configuration
echo ""
echo "Generating default configuration..."
cat > config/nexus_config.json << 'EOF'
{
    "platform": {
        "name": "NexusAI",
        "version": "1.0.0",
        "token_strategy": "balanced"
    },
    "token_management": {
        "global_pool": 100000,
        "default_max_tokens": 4096,
        "reset_interval_hours": 24
    },
    "agents": {
        "auto_discovery": true,
        "heartbeat_interval_seconds": 30,
        "stale_timeout_seconds": 300
    },
    "performance": {
        "apple_silicon_optimized": true,
        "metal_acceleration": true,
        "memory_limit_mb": 2048
    }
}
EOF
echo "✓ Configuration generated"

# Create sample agent template
echo ""
echo "Creating sample agent template..."
cat > agents/sample_agent.py << 'EOF'
"""
Sample Agent Template for NexusAI Platform
Copy this file to create your own custom agent
"""

from NexusCore.agent_registry import AgentInfo, AgentCapability, AgentStatus


def create_sample_agent():
    """Create a sample agent instance"""
    return AgentInfo(
        agent_id="my-custom-agent-01",
        agent_type="custom",
        name="My Custom Agent",
        description="A custom AI agent for NexusAI platform",
        capabilities=[
            AgentCapability(
                name="custom_task",
                description="Perform custom tasks",
                input_types=["text"],
                output_types=["text"],
                cost_estimate=1.0
            )
        ],
        status=AgentStatus.AVAILABLE
    )


async def execute_task(input_data, tokens):
    """
    Execute a task with the given input and token budget
    
    Args:
        input_data: The input data for the task
        tokens: Number of tokens allocated for this task
    
    Returns:
        The result of the task execution
    """
    # Your custom implementation here
    result = f"Processed: {input_data}"
    return result


if __name__ == "__main__":
    agent = create_sample_agent()
    print(f"Created agent: {agent.name}")
    print(f"Capabilities: {[c.name for c in agent.capabilities]}")
EOF
echo "✓ Sample agent template created"

# Make run script executable
chmod +x run.sh 2>/dev/null || true

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the demo: python -m NexusCore.main"
echo "3. Add your custom agents to the 'agents' directory"
echo "4. Configure settings in 'config/nexus_config.json'"
echo ""
echo "For macOS optimization:"
echo "- Ensure you're running macOS 13.0+ for best performance"
echo "- Apple Silicon (M1/M2/M3) chips are fully optimized"
echo "- Metal acceleration is enabled by default"
echo ""
