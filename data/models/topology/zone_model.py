"""Zone model for network simulation"""
from typing import List, Tuple, Literal
from pydantic import BaseModel

from data.models.topology.node_model import AdapterModal, NetworkModal

class ZoneModal(BaseModel):
    """Security zone containing networks"""
    name: str
    type: Literal["SECURE"]
    size: Tuple[float, float]
    position: Tuple[float, float]
    networks: List[NetworkModal]
    adapters: List[AdapterModal]