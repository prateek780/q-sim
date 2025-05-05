import uuid
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Union, Any
from redis_om import JsonModel, Field

from data.models.connection.redis import get_redis_conn

class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class AgentExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

class ChatLogMetadata(JsonModel):
    """Metadata for a single conversation."""
    conversation_id: str = Field(index=True, primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = Field(index=True, default='default')
    start_time: datetime = Field(index=True, default_factory=datetime.now)
    last_updated: datetime = Field(index=True, default_factory=datetime.now)
    title: Optional[str] = Field(index=True, default=None) # Index title for searching

    class Meta:
        database = get_redis_conn()
        global_key_prefix = "network-sim"
        model_key_prefix = "chat-log-meta"

class ChatMessage(JsonModel):
    """Represents a standard chat message within a conversation."""
    message_id: str = Field(index=True, primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(index=True) # Link back to the conversation metadata
    timestamp: datetime = Field(index=True, default_factory=datetime.now)
    role: MessageRole = Field(index=True)
    content: str = Field(full_text_search=True, default="") # Enable full-text search on content

    class Meta:
        database = get_redis_conn()
        global_key_prefix = "network-sim"
        model_key_prefix = "chat-message"

class AgentTurn(JsonModel):
    """Represents an agent execution turn within a conversation."""
    conversation_id: str = Field(index=True)
    timestamp: datetime = Field(index=True, default_factory=datetime.now)
    start_timestamp: datetime = Field(index=True, default_factory=datetime.now)
    agent_id: str = Field(index=True)
    task_id: Optional[str] = Field(index=True, default=None)
    status: AgentExecutionStatus = Field(index=True, default=AgentExecutionStatus.PENDING)
    agent_input: Dict[str, Any] = Field(default={}, index=False)
    agent_output: Optional[Dict[str, Any]] = Field(default=None, index=False)

    error_message: Optional[str] = Field(default=None)

    class Meta:
        database = get_redis_conn()
        global_key_prefix = "network-sim"
        model_key_prefix = "agent-turn"

# --- Type alias for history items ---
HistoryItem = Union[ChatMessage, AgentTurn]