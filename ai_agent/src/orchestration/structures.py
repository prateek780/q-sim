from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from ai_agent.src.agents.enums import AgentTaskType
from ai_agent.src.consts.agent_type import AgentType


class RoutingOutput(BaseModel):
    """Structured output for agent routing decision."""
    agent_id: Optional[AgentType] = Field(
        None,
        description="The unique ID of the selected agent. Null if no suitable agent was found."
    )
    task_id: Optional[AgentTaskType] = Field(
        description=f"Task ID for the selected agent's selected task. (For example Task ID for summarizing logs is '{AgentTaskType.LOG_SUMMARIZATION.value}' for {AgentType.LOG_SUMMARIZER.value} agent)"
    )
    input_data: Dict[str, Any] = Field(
        description="The original user query that was evaluated."
    )
    reason: str = Field(
        description="Explanation of why the specific agent was chosen, or why no agent was deemed suitable."
    )
    suggestion: Optional[str] = Field(
        None,
        description="A suggestion to help the user if no suitable agent was found (e.g., rephrase query, list available functions)."
    )
    agent_response: Optional[Any] = None