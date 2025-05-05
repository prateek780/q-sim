from typing import Optional
from pydantic import BaseModel, Field


class BaseAgentInput(BaseModel):
    conversation_id: str = Field(description="Unique identifier for the conversation.")

class BaseAgentOutput(BaseModel):
    message_id : Optional[str] = Field(description="Unique identifier for the output message.", default=None)