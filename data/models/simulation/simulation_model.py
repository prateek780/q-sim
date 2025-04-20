"""Simulation model for network simulation"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel
from redis_om import JsonModel, Field as RedisField, Migrator

from data.models.connection.redis import get_redis_conn
from data.models.topology.world_model import WorldModal

class SimulationStatus(str, Enum):
    """Status of a simulation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PerformanceMetrics(BaseModel):
    """Performance metrics for a simulation"""
    total_messages: int = 0
    average_latency: float = 0.0
    throughput: float = 0.0
    congestion_events: int = 0
    packet_loss: float = 0.0
    runtime_seconds: float = 0.0

class SimulationModal(JsonModel):
    """Model representing a network simulation run"""
    name: str = RedisField(index=True)
    world_id: str = RedisField(index=True)
    status: SimulationStatus = RedisField(index=True, default=SimulationStatus.PENDING)
    start_time: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    end_time: Optional[datetime] = None
    configuration: WorldModal = None
    metrics: Optional[PerformanceMetrics] = PerformanceMetrics()
    
    class Meta:
        global_key_prefix = "network-sim"
        model_key_prefix = "simulation"
        database = get_redis_conn()

def save_simulation(simulation_data: Union[Dict[str, Any], SimulationModal]) -> str:
    """Save simulation data to Redis"""
    # Ensure we have a connection
    get_redis_conn()
    
    # Ensure indexes are created
    Migrator().run()
    
    # Create Simulation instance
    if isinstance(simulation_data, dict):
        simulation = SimulationModal(**simulation_data)
    elif isinstance(simulation_data, SimulationModal):
        simulation = simulation_data
    
    simulation.last_updated = datetime.now()
    # Save to Redis
    simulation.save()
    
    return simulation.pk

def get_simulation(primary_key: str) -> Optional[SimulationModal]:
    """Retrieve simulation data from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()
    
    try:
        return SimulationModal.get(primary_key)
    except Exception as e:
        print(f"Error retrieving simulation data: {e}")
        return None

def get_simulations_by_world(world_id: str) -> List[SimulationModal]:
    """Get all simulations for a specific world"""
    # Ensure we have a connection
    get_redis_conn()
    
    return SimulationModal.find(SimulationModal.world_id == world_id).all()

def update_simulation_status(simulation_id: str, status: SimulationStatus) -> bool:
    """Update the status of a simulation"""
    # Ensure we have a connection
    get_redis_conn()
    
    try:
        simulation = SimulationModal.get(simulation_id)
        simulation.status = status
        simulation.last_updated = datetime.now()
        
        # Update timestamps based on status
        if status == SimulationStatus.RUNNING and not simulation.start_time:
            simulation.start_time = datetime.now()
        elif status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED, SimulationStatus.CANCELLED]:
            simulation.end_time = datetime.now()
            
        simulation.save()
        return True
    except Exception as e:
        print(f"Error updating simulation status: {e}")
        return False

def update_simulation_metrics(simulation_id: str, metrics: Dict[str, Any]) -> bool:
    """Update the metrics of a simulation"""
    # Ensure we have a connection
    get_redis_conn()
    
    try:
        simulation = SimulationModal.get(simulation_id)
        
        # Update metrics
        for key, value in metrics.items():
            if hasattr(simulation.metrics, key):
                setattr(simulation.metrics, key, value)
        
        simulation.save()
        return True
    except Exception as e:
        print(f"Error updating simulation metrics: {e}")
        return False

def delete_simulation(primary_key: str) -> bool:
    """Delete simulation data from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()
    
    try:
        simulation = SimulationModal.get(primary_key)
        simulation.delete()
        return True
    except Exception as e:
        print(f"Error deleting simulation data: {e}")
        return False