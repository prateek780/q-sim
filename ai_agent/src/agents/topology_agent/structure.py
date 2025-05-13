from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

from ai_agent.src.agents.base.base_structures import BaseAgentInput, BaseAgentOutput
from data.models.topology.world_model import WorldModal


class OptimizeTopologyRequest(BaseAgentInput):
    world_id: str = Field(description="The ID of the world to optimize.")
    optional_instructions: Optional[str] = Field(
        description="Optional instructions for the optimization process."
    )


class OptimizeStep(BaseModel):
    change_path: List[str] = Field(description="JSON path(s) changed in the network.")
    change: str = Field(description="Change made to the topology.")
    reason: str = Field(description="Reason for the change.")
    citation: Optional[List[str]] = Field(
        description="External/Internal citation supporting the reason."
    )
    comments: Optional[str] = Field(
        description="Additional comments about the optimization process."
    )


class OptimizeTopologyOutput(BaseAgentOutput):
    error: Optional[str] = Field(description="Error message if any occurred during the optimization.")
    success: bool = Field(description="Indicates whether the optimization was successful.", default=True)
    original_topology: WorldModal = Field(
        description="The original network topology before optimization."
    )
    optimized_topology: WorldModal = Field(
        description="The optimized network topology."
    )
    overall_feedback: str = Field(
        description="Overall feedback on the current topology."
    )
    cost: float = Field(description="The cost of the optimized topology.")
    optimization_steps: List[OptimizeStep] = Field(
        description="Steps taken during the optimization process."
    )

class SynthesisTopologyRequest(BaseAgentInput):
    user_query: str = Field(description="Instructions for optimizing the topology.")
    regeneration_feedback: Optional[str] = Field(
        None,
        description=(
            "Optional consolidated feedback and specific instructions from a prior validation step, "
            "to be used by the Topology Generator Agent if this is a retry attempt. "
            "This feedback aims to guide the agent towards correcting previously identified issues "
            "or clarifying ambiguities from the original user_query."
        )
    )

class SynthesisTopologyOutput(BaseAgentOutput):
    error: Optional[str] = Field(description="Error message if any occurred during the synthesis.")
    success: bool = Field(description="Indicates whether the synthesis was successful.", default=True)
    generated_topology: WorldModal = Field(
        description="The synthesized network topology."
    )
    overall_feedback: str = Field(description="Overall feedback on the current topology.")
    cost: float = Field(description="The cost of the synthesized topology.")
    thought_process: List[str] = Field(
        description="Thought process leading to the synthesis.",
        default=[]
    )
    input_query: str = Field(description="The original user query.")

class TopologyQnARequest(BaseAgentInput):
    user_query: str = Field(description="Instructions for optimizing the topology.")
    world_id: str = Field(description="The ID of the world to optimize.")
    optional_instructions: Optional[str] = Field(
        description="Optional instructions for the optimization process."
    )

class RelevantTopologyPart(BaseModel):
    path: str
    snippet: Optional[Union[str, Dict, List]]


class TopologyQnAOutput(BaseModel):
    status: Literal["answered", "clarification_needed", "error", "unanswerable"] = Field(description="The outcome status of the QnA attempt.")
    answer: str = Field(description="The natural language answer if status is 'answered'; the clarifying question if status is 'clarification_needed'; or an error/unanswerable message if status is 'error' or 'unanswerable'.")
    relevant_topology_parts: Optional[List[RelevantTopologyPart]] = Field(None, description="List of references to specific parts of the topology data that support the answer, only if status is 'answered'.")
    error_message: Optional[str] = Field(None, description="Specific error details if status is 'error'.")