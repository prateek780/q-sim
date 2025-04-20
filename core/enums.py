import enum


class ZoneType(enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    SECURE = "secure"
    # Add more types as needed

class NodeType(enum.Enum):
    INTERNET_EXCHANGE = "internet_exchange"
    CLASSICAL_HOST = "classical_host"
    CLASSICAL_ROUTER = "classical_router"
    C2Q_CONVERTER = "c2q_converter"
    Q2C_CONVERTER = "q2c_converter"
    QUANTUM_HOST = "quantum_host"
    QUANTUM_REPEATER = "quantum_repeater"
    NETWORK = "network"
    QUANTUM_ADAPTER = "quantum_adapter"

class NetworkType(enum.Enum):
    QUANTUM_NETWORK = "quantum_network"
    CLASSICAL_NETWORK = "classical_network"

class SimulationEventType(enum.Enum):
    PACKET_TRANSMITTED = "packet_transmitted"
    PACKET_RECEIVED = "packet_received"
    DATA_SENT = "data_sent"
    DATA_RECEIVED = "data_received"
    PACKET_ROUTED = "packet_routed"
    QKD_INITIALIZED = "qkd_initiated"
    CLASSICAL_DATA_RECEIVED = "classical_data_received"