from typing import List, Optional
from pydantic import BaseModel

from ai_agent.src.consts.agent_type import AgentType


class AgentInteractionRequest(BaseModel):
    agent_id: AgentType


class LogSummaryRequest(AgentInteractionRequest):
    simulation_id: str = "01JSMD4079X4VYT3JPN60ZWHHY"  # TODO: Remove when done testing
    message: str
    tags: Optional[List[str]] = None


class AgentRouterRequest(AgentInteractionRequest):
    simulation_id: str = "01JSMD4079X4VYT3JPN60ZWHHY"
    user_query: str
