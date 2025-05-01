from typing import List, Optional, Tuple, Literal
from pydantic import BaseModel, Field

class ConnectionModal(BaseModel):
    """Network connection between hosts"""
    from_node: str = Field(description="Name of the host from which the connection originates")
    to_node: str = Field(description="Name of the host to which the connection ends")
    bandwidth: int = Field(description="Bandwidth of the connection in Mbps")
    latency: int = Field(description="Latency of the connection in milliseconds")
    length: float = Field(description="Length of the connection in kilometers")
    loss_per_km: float = Field(description="Loss per kilometer of the connection")
    noise_model: str = Field(description="Noise model for the connection")
    name: str = Field(description="Name of the connection")

class HostModal(BaseModel):
    """Base class for network hosts"""
    name: str = Field(description="Name of the host")
    type: str = Field(description="Type of the host (e.g., SERVER, CLIENT)")
    address: Optional[str] = Field(description="Address of the host. This can be IP/Hostname")
    location: Tuple[float, float] = Field(description="Location of the host in (x, y) coordinates")

class NetworkModal(BaseModel):
    """Network containing hosts and connections"""
    name: str = Field(description="Name of the network")
    address: str = Field(description="Address of the network. This can be IP/Hostname")
    type: Literal["CLASSICAL_NETWORK", "QUANTUM_NETWORK"]
    location: Tuple[float, float] = Field(description="Location of the network in (x, y) coordinates")
    hosts: List[HostModal] = Field(description="List of hosts within the network")
    connections: List[ConnectionModal] = Field(description="List of connections within the network")

class AdapterModal(BaseModel):
    """Quantum adapter connecting classical and quantum networks"""
    name: str = Field(description="Name of the adapter")
    type: str = Field(description="Type of the adapter (e.g., QUMO, CNOT)")
    # size: Optional[Tuple[float, float]] = Field(description="Size of the adapter in (x, y) coordinates")
    address: str = Field(description="Address of the host. This can be IP/Hostname")
    location: Tuple[float, float] = Field(description="Location of the adapter in (x, y) coordinates")
    quantumHost: str = Field(description="Address of the host where the quantum network is connected")
    classicalHost: str = Field(description="Address of the host where the classical network is connected")
    classicalNetwork: str = Field(description="Name of the classical network")
    quantumNetwork: str = Field(description="Name of the quantum network")