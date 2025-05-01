from typing import List, Optional
from pydantic import BaseModel, Field

from data.models.topology.world_model import WorldModal


class OptimizeTopologyRequest(BaseModel):
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


class OptimizeTopologyOutput(BaseModel):
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

class SynthesisTopologyRequest(BaseModel):
    user_query: str = Field(description="Instructions for optimizing the topology.")

class SynthesisTopologyOutput(BaseModel):
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