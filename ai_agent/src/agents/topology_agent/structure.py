from typing import List, Optional
from pydantic import BaseModel, Field

from data.models.topology.world_model import WorldModal


class OptimizeTopologyRequest(BaseModel):
    world_id: str = Field(description="The ID of the world to optimize.")
    optional_instructions: Optional[str] = Field(description="Optional instructions for the optimization process.")

class OptimizeStep(BaseModel):
    change: str = Field(description="Change made to the topology.")
    reason: str = Field(description="Reason for the change.")
    citation: Optional[List[str]] = Field(description="Citation supporting the reason.")
    comments: Optional[str] = Field(description="Additional comments about the optimization process.")

class OptimizeTopologyOutput(BaseModel):
    topology: WorldModal = Field(description="The optimized network topology.")
    cost: float = Field(description="The cost of the optimized topology.")
    optimization_steps: List[OptimizeStep] = Field(description="Steps taken during the optimization process.")