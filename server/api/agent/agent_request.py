from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.topology_agent.structure import SynthesisTopologyRequest
from ai_agent.src.consts.agent_type import AgentType


class AgentInteractionRequest(BaseModel):
    agent_id: AgentType
    task_id: Optional[AgentTaskType] = None
    conversation_id: str

class LogSummaryRequest(AgentInteractionRequest):
    simulation_id: str = "01JSMD4079X4VYT3JPN60ZWHHY"  # TODO: Remove when done testing
    message: Optional[str] = None
    tags: Optional[List[str]] = None

class AgentRouterRequest(AgentInteractionRequest):
    user_query: str
    extra_kwargs: Optional[Dict[str, Any]] = None

class TopologyOptimizeRequest(AgentInteractionRequest):
    world_id: Optional[str] = "01JSMD3F6SZF664Y71V5Z5DCKG"
    optional_instructions: Optional[str] = None

class SynthesizeTopologyRequest(AgentInteractionRequest, SynthesisTopologyRequest):
    pass
