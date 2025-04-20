from data.models.topology.node_model import ConnectionModal, HostModal, NetworkModal, AdapterModal
from data.models.topology.zone_model import ZoneModal
from data.models.topology.world_model import WorldModal

from redis_om import Migrator

__all__ = ['ConnectionModal', 'HostModal', 'NetworkModal', 'AdapterModal', 'ZoneModal', 'WorldModal']

def run_migrator():
    # Ensure indexes are created
    Migrator().run()

run_migrator()