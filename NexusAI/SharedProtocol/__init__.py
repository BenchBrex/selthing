"""
SharedProtocol - Standardized communication protocol for inter-agent messaging
Ensures all agents can understand and coordinate with each other
"""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


class MessageType(Enum):
    """Types of messages that can be exchanged between agents"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    STATUS_UPDATE = "status_update"
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class MessageHeader:
    """Standard message header for all inter-agent communication"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: MessageType = MessageType.TASK_REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    ttl: int = 60  # Time to live in seconds
    correlation_id: Optional[str] = None  # For request-response pairing
    
    def is_expired(self) -> bool:
        return time.time() > self.timestamp + self.ttl
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MessageHeader':
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            message_type=MessageType(data.get("message_type", "task_request")),
            priority=MessagePriority(data.get("priority", 5)),
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", 60),
            correlation_id=data.get("correlation_id")
        )


@dataclass
class TaskPayload:
    """Payload for task-related messages"""
    task_id: str
    description: str
    input_data: Any
    input_types: List[str]
    output_types: List[str]
    constraints: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "input_data": self.input_data,
            "input_types": self.input_types,
            "output_types": self.output_types,
            "constraints": self.constraints,
            "deadline": self.deadline,
            "dependencies": self.dependencies
        }


@dataclass
class TaskResultPayload:
    """Payload for task result messages"""
    task_id: str
    success: bool
    output: Any
    tokens_used: int
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "tokens_used": self.tokens_used,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "error_message": self.error_message
        }


@dataclass
class CapabilityPayload:
    """Payload for capability exchange messages"""
    agent_id: str
    capabilities: List[Dict[str, Any]]
    availability: bool = True
    current_load: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "availability": self.availability,
            "current_load": self.current_load
        }


@dataclass
class StatusPayload:
    """Payload for status update messages"""
    agent_id: str
    status: str  # "available", "busy", "offline", "error"
    current_task: Optional[str] = None
    queue_length: int = 0
    last_updated: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task": self.current_task,
            "queue_length": self.queue_length,
            "last_updated": self.last_updated
        }


@dataclass
class CoordinationPayload:
    """Payload for coordination messages between agents"""
    coordination_type: str  # "handoff", "collaboration", "delegation"
    initiating_agent: str
    target_agents: List[str]
    context: Dict[str, Any]
    proposed_plan: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        return {
            "coordination_type": self.coordination_type,
            "initiating_agent": self.initiating_agent,
            "target_agents": self.target_agents,
            "context": self.context,
            "proposed_plan": self.proposed_plan
        }


@dataclass
class NexusMessage:
    """
    Complete message structure for inter-agent communication
    Follows a standardized format that all agents understand
    """
    header: MessageHeader
    payload: Any
    version: str = "1.0"
    signature: Optional[str] = None  # For message authentication
    
    def serialize(self) -> str:
        """Serialize message to JSON string"""
        data = {
            "version": self.version,
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict() if hasattr(self.payload, 'to_dict') else self.payload,
            "signature": self.signature
        }
        return json.dumps(data)
    
    @classmethod
    def deserialize(cls, json_str: str) -> 'NexusMessage':
        """Deserialize message from JSON string"""
        data = json.loads(json_str)
        
        header = MessageHeader.from_dict(data["header"])
        
        # Determine payload type based on message type
        payload_data = data["payload"]
        payload = payload_data  # Default to raw dict
        
        if header.message_type == MessageType.TASK_REQUEST:
            payload = TaskPayload(**payload_data)
        elif header.message_type == MessageType.TASK_RESPONSE:
            payload = TaskResultPayload(**payload_data)
        elif header.message_type in [MessageType.CAPABILITY_QUERY, MessageType.CAPABILITY_RESPONSE]:
            payload = CapabilityPayload(**payload_data)
        elif header.message_type == MessageType.STATUS_UPDATE:
            payload = StatusPayload(**payload_data)
        elif header.message_type in [MessageType.COORDINATION_REQUEST, MessageType.COORDINATION_RESPONSE]:
            payload = CoordinationPayload(**payload_data)
        
        return cls(
            header=header,
            payload=payload,
            version=data.get("version", "1.0"),
            signature=data.get("signature")
        )
    
    def validate(self) -> bool:
        """Validate message integrity"""
        # Check if message is expired
        if self.header.is_expired():
            return False
        
        # Check required fields
        if not self.header.sender_id:
            return False
        
        # Verify message type matches payload
        expected_payloads = {
            MessageType.TASK_REQUEST: TaskPayload,
            MessageType.TASK_RESPONSE: TaskResultPayload,
            MessageType.STATUS_UPDATE: StatusPayload
        }
        
        if self.header.message_type in expected_payloads:
            if not isinstance(self.payload, expected_payloads[self.header.message_type]):
                return False
        
        return True


class MessageBus:
    """
    Simple message bus for inter-agent communication
    In production, this would be replaced with a more robust message queue system
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List callable] = {}
        self.message_queue: List[NexusMessage] = []
        self._running = False
    
    def subscribe(self, agent_id: str, callback: callable):
        """Subscribe an agent to receive messages"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
    
    def unsubscribe(self, agent_id: str, callback: callable):
        """Unsubscribe an agent from receiving messages"""
        if agent_id in self.subscribers:
            self.subscribers[agent_id] = [c for c in self.subscribers[agent_id] if c != callback]
    
    def publish(self, message: NexusMessage):
        """Publish a message to the bus"""
        if not message.validate():
            raise ValueError("Invalid message")
        
        self.message_queue.append(message)
        
        # Deliver to specific receiver if specified
        if message.header.receiver_id and message.header.receiver_id in self.subscribers:
            for callback in self.subscribers[message.header.receiver_id]:
                callback(message)
        else:
            # Broadcast to all subscribers
            for agent_id, callbacks in self.subscribers.items():
                if agent_id != message.header.sender_id:
                    for callback in callbacks:
                        callback(message)
    
    def get_pending_messages(self, agent_id: str) -> List[NexusMessage]:
        """Get pending messages for a specific agent"""
        return [
            msg for msg in self.message_queue
            if msg.header.receiver_id == agent_id or msg.header.receiver_id == ""
        ]
    
    def clear_processed(self, message_id: str):
        """Remove a processed message from the queue"""
        self.message_queue = [m for m in self.message_queue if m.message_id != message_id]


# Convenience functions for creating common message types

def create_task_request(sender_id: str, receiver_id: str, 
                       task_id: str, description: str,
                       input_data: Any, input_types: List[str],
                       output_types: List[str],
                       priority: MessagePriority = MessagePriority.NORMAL) -> NexusMessage:
    """Create a task request message"""
    header = MessageHeader(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=MessageType.TASK_REQUEST,
        priority=priority
    )
    
    payload = TaskPayload(
        task_id=task_id,
        description=description,
        input_data=input_data,
        input_types=input_types,
        output_types=output_types
    )
    
    return NexusMessage(header=header, payload=payload)


def create_task_response(sender_id: str, receiver_id: str,
                        task_id: str, success: bool,
                        output: Any, tokens_used: int,
                        execution_time: float,
                        correlation_id: str,
                        error_message: Optional[str] = None) -> NexusMessage:
    """Create a task response message"""
    header = MessageHeader(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=MessageType.TASK_RESPONSE,
        correlation_id=correlation_id
    )
    
    payload = TaskResultPayload(
        task_id=task_id,
        success=success,
        output=output,
        tokens_used=tokens_used,
        execution_time=execution_time,
        error_message=error_message
    )
    
    return NexusMessage(header=header, payload=payload)


def create_status_update(agent_id: str, status: str,
                        current_task: Optional[str] = None,
                        queue_length: int = 0) -> NexusMessage:
    """Create a status update message"""
    header = MessageHeader(
        sender_id=agent_id,
        message_type=MessageType.STATUS_UPDATE
    )
    
    payload = StatusPayload(
        agent_id=agent_id,
        status=status,
        current_task=current_task,
        queue_length=queue_length
    )
    
    return NexusMessage(header=header, payload=payload)
