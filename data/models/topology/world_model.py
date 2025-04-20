"""World model for network simulation"""
from typing import List, Tuple, Dict, Any, Optional, Union
from redis_om import JsonModel, Field as RedisField, Migrator

from data.models.connection.redis import get_redis_conn
from data.models.topology.zone_model import ZoneModal

class WorldModal(JsonModel):
    """Root model representing the entire simulation world"""
    name: str = RedisField(index=True)
    size: Tuple[float, float]
    zones: List[ZoneModal]
    
    class Meta:
        global_key_prefix = "network-sim"
        model_key_prefix = "world"
        database = get_redis_conn()

def save_world_to_redis(world: Union[Dict[str, Any], WorldModal]) -> str:
    """Save world data to Redis"""
    # Ensure we have a connection
    get_redis_conn()
    
    # Ensure indexes are created
    Migrator().run()
    
    # Create World instance
    if isinstance(world, dict):
        world = WorldModal(**world)
    
    # Save to Redis
    world.save()
    
    return world.pk

def get_topology_from_redis(primary_key: str) -> Optional[WorldModal]:
    """Retrieve world data from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()
    
    try:
        return WorldModal.get(primary_key)
    except Exception as e:
        print(f"Error retrieving world data: {e}")
        return None

def get_all_topologies_from_redis() -> List[WorldModal]:
    """Retrieve all worlds from Redis"""
    # Ensure we have a connection
    get_redis_conn()
    
    return WorldModal.find().all()

def delete_topology_from_redis(primary_key: str) -> bool:
    """Delete world data from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()
    
    try:
        world = WorldModal.get(primary_key)
        world.delete()
        return True
    except Exception as e:
        print(f"Error deleting world data: {e}")
        return False