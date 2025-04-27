from typing import List, Optional
from pydantic import BaseModel

from ai_agent.src.consts.agent_type import AgentType


class AgentInteractionRequest(BaseModel):
    simulation_id: str = "01JSMD4079X4VYT3JPN60ZWHHY" #TODO: Remove when done testing
    agent_id: AgentType
    message: str
    tags: Optional[List[str]] = None