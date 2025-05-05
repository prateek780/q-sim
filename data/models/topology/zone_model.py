"""Zone model for network simulation"""
from typing import List, Tuple, Literal
from pydantic import BaseModel, Field

from data.models.topology.node_model import AdapterModal, NetworkModal

class ZoneModal(BaseModel):
    """Security zone containing networks"""
    name: str = Field(description="Name of the zone")
    type: Literal["SECURE"]= Field(description="Secure/Non-Secure Zone")
    size: Tuple[float, float]= Field(description="Size of the zone world in (x, y) coordinates")
    position: Tuple[float, float]= Field(description="Position of the zone world in (x, y) coordinates")
    networks: List[NetworkModal]= Field(description="List of networks within the zone")
    adapters: List[AdapterModal]= Field(description="List of 'Quantum to Classical adapters' within the zone")
