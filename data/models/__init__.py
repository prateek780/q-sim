from data.models.conversation.conversation_model import (
    AgentTurn,
    ChatLogMetadata,
    ChatMessage,
)
from data.models.simulation.simulation_model import SimulationModal
from data.models.topology.node_model import (
    ConnectionModal,
    HostModal,
    NetworkModal,
    AdapterModal,
)
from data.models.topology.zone_model import ZoneModal
from data.models.topology.world_model import WorldModal

from redis_om import Migrator

__all__ = [
    ConnectionModal,
    HostModal,
    NetworkModal,
    AdapterModal,
    ZoneModal,
    WorldModal,
    SimulationModal,
    AgentTurn,
    ChatMessage,
    ChatLogMetadata,
]


def run_migrator():
    print("Running migrations...")
    Migrator().run()


run_migrator()
