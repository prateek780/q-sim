from typing import List, Optional, Tuple, Literal
from pydantic import BaseModel, Field

class ConnectionModal(BaseModel):
    """Network connection between hosts"""
    from_node: str
    to_node: str
    bandwidth: int
    latency: int
    length: float
    loss_per_km: float
    noise_model: str
    name: str

class HostModal(BaseModel):
    """Base class for network hosts"""
    name: str
    type: str
    address: str
    location: Tuple[float, float]

class NetworkModal(BaseModel):
    """Network containing hosts and connections"""
    name: str
    address: str
    type: Literal["CLASSICAL_NETWORK", "QUANTUM_NETWORK"]
    location: Tuple[float, float]
    hosts: List[HostModal]
    connections: List[ConnectionModal]

class AdapterModal(BaseModel):
    """Quantum adapter connecting classical and quantum networks"""
    name: str
    type: str
    address: str
    location: Tuple[float, float]
    quantumHost: str
    classicalHost: str
    classicalNetwork: str
    quantumNetwork: str