import time
from typing import TYPE_CHECKING

from core.enums import SimulationEventType
from data.models.simulation.log_model import LogLevel
from utils.encoding import transform_val

if TYPE_CHECKING:
    from core.s_object import Sobject


class Event:
    def __init__(self, event_type: SimulationEventType, node: 'Sobject', **kwargs):
        self.event_type = event_type
        self.node = node
        self.timestamp = time.time()
        self.data = kwargs
        self.log_level = kwargs.get("log_level", LogLevel.INFO)

    def to_dict(self):
        return {
            "event_type": self.event_type.value,
            "node": self.node.name,
            "timestamp": self.timestamp,
            "data": {k: transform_val(v) for k, v in self.data.items()},
        }
