import asyncio
from datetime import datetime
from pprint import pprint
import threading
from typing import Optional, Dict, Any
import traceback

from core.base_classes import World
from core.event import Event
from data.embedding.embedding_util import EmbeddingUtil
from data.models.simulation.log_model import add_log_entry
from data.models.simulation.simulation_model import (
    SimulationModal,
    SimulationStatus,
    save_simulation,
    update_simulation_status,
)
from data.models.topology.world_model import WorldModal
from json_parser import simulate_from_json
from server.socket_server.socket_server import ConnectionManager


class SimulationManager:
    _instance: Optional["SimulationManager"] = None
    simulation_world: World = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SimulationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.is_running = False
        self.socket_conn = ConnectionManager()
        self.current_simulation = None
        self.simulation_data: SimulationModal = None
        self.main_event_loop = None
        self.embedding_util = EmbeddingUtil(embedding_provider="openai")

    @classmethod
    def get_instance(cls) -> "SimulationManager":
        """Get or create the singleton instance"""
        if cls._instance is None:
            return cls()
        return cls._instance

    @classmethod
    def destroy_instance(cls) -> None:
        """Reset the singleton instance"""
        if cls._instance is not None:
            cls._instance.stop()
            cls._instance = None

    def start_simulation(self, network: WorldModal) -> bool:
        if self.is_running:
            return False

        try:
            # Set simulation state
            self.is_running = True
            # self.simulation_data = {
            #     "network_id": network.pk,
            #     "network_config": network.model_dump(),
            #     "progress": 0,
            #     "status": "running",
            #     "results": None,
            #     "error": None,
            # }
            self.simulation_data = SimulationModal(
                world_id=network.pk,
                name=network.name,
                status=SimulationStatus.PENDING,
                start_time=datetime.now(),
                end_time=None,
                configuration=network,
                metrics=None,
            )
            self.save_simulation = save_simulation(self.simulation_data)
            try:
                self.main_event_loop = asyncio.get_running_loop()
                print(f"Captured main event loop: {self.main_event_loop}")
            except RuntimeError:
                print(
                    "CRITICAL WARNING: Could not get running loop when starting simulation. "
                    "Ensure start_simulation is called from an async context (e.g., await manager.start_simulation). "
                    "Event broadcasting will likely fail."
                )
                self.main_event_loop = None  # Ensure it's None if failed
            # Start the simulation process
            self._run_simulation(network)

            return True

        except Exception as e:
            self.emit_event(
                "simulation_error",
                {
                    "message": f"Error starting simulation: {str(e)}",
                    "traceback": traceback.format_exc(),
                },
            )
            raise

    def on_update(self, event: Event) -> None:
        self.emit_event("simulation_event", event)
        log_entry = add_log_entry(
            {
                "simulation_id": self.simulation_data.pk,
                "timestamp": datetime.now(),
                "level": event.log_level,
                "component": event.node.name,
                "entity_type": getattr(event.node, "type", None),
                "details": event.to_dict(),
            }
        )
        self.embedding_util.embed_and_store_log(log_entry)

    def _run_simulation(self, topology_data: WorldModal) -> None:
        """
        Run the actual simulation process
        This would be where your simulation logic lives
        """
        try:
            import time
            from threading import Thread

            def simulation_worker():
                try:
                    self.emit_event(
                        "simulation_started", {"time": datetime.now().timestamp()}
                    )

                    # Mark as running
                    self.simulation_data.status = SimulationStatus.RUNNING
                    update_simulation_status(
                        self.simulation_data.pk, SimulationStatus.RUNNING
                    )
                    self.simulation_world = simulate_from_json(
                        topology_data.model_dump(), self.on_update
                    )

                    while self.simulation_world.is_running:
                        time.sleep(5)

                    self.emit_event(
                        "simulation_completed",
                        {"results": self.simulation_data["results"]},
                    )
                    self.simulation_data.status = SimulationStatus.COMPLETED
                    update_simulation_status(
                        self.simulation_data.pk, SimulationStatus.COMPLETED
                    )

                except Exception as e:
                    self._handle_error(e)
                    self.simulation_data.status = SimulationStatus.FAILED
                    update_simulation_status(
                        self.simulation_data.pk, SimulationStatus.FAILED
                    )

                finally:
                    # Reset run state if this wasn't from an external stop
                    if self.is_running:
                        self.is_running = False

            # Run simulation in background
            Thread(target=simulation_worker).start()

        except Exception as e:
            self._handle_error(e)

    def send_message_command(
        self, from_node_name: str, to_node_name: str, message: str
    ):
        from_node = to_node = None
        for network in self.simulation_world.networks:
            for node in network.nodes:
                if node.name == from_node_name:
                    from_node = node
                    continue
                if node.name == to_node_name:
                    to_node = node
                    continue

        if not (from_node and to_node):
            print(from_node, to_node)
            self.emit_event(
                "simulation_error", {"error": "Nodes not found for sending message"}
            )
            return

        print("Send Message B/W ", from_node, " And ", to_node)

        from_node.send_data(message, to_node)

    def stop(self) -> None:
        """Stop the running simulation"""
        if not self.is_running:
            return

        self.is_running = False

        if self.current_simulation is not None:
            # Add logic to safely stop your simulation
            # self.current_simulation.stop()
            self.current_simulation = None

        self.simulation_data.status = SimulationStatus.COMPLETED
        update_simulation_status(self.simulation_data.pk, SimulationStatus.COMPLETED)
        self.simulation_world.stop()

    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        return {
            "is_running": self.is_running,
            "progress": self.simulation_data.get("progress", 0),
            "status": self.simulation_data.get("status", "idle"),
            "results": self.simulation_data.get("results"),
            "error": self.simulation_data.get("error"),
        }

    def emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emit event to connected clients via Socket using run_coroutine_threadsafe.
        This method is designed to be called safely FROM A WORKER THREAD.

        Args:
            event: Event name
            data: Event data
        """
        # Check if we have the connection manager and the main loop reference
        if not self.socket_conn:
            print(
                f"[{threading.current_thread().name}] Warning: Socket connection manager not available. Cannot emit '{event}'."
            )
            return
        if not self.main_event_loop or not self.main_event_loop.is_running():
            print(
                f"[{threading.current_thread().name}] Warning: Main event loop not available or not running. Cannot emit '{event}'."
            )
            return

        try:
            if hasattr(data, "to_dict"):
                data = data.to_dict()
        except Exception as e:
            print(
                f"[{threading.current_thread().name}] Error serializing data for event '{event}': {e}"
            )
            pprint(data)
            return

        coro_to_run = self.socket_conn.broadcast(dict(event=event, data=data))
        future = asyncio.run_coroutine_threadsafe(coro_to_run, self.main_event_loop)

        print(
            f"[{threading.current_thread().name}] Submitted broadcast for event '{event}' to main loop."
        )

    def _handle_error(self, error: Exception) -> None:
        """
        Handle simulation errors

        Args:
            error: The exception that occurred
        """
        error_info = {"message": str(error), "traceback": traceback.format_exc()}

        self.simulation_data["status"] = "error"
        self.simulation_data["error"] = error_info
        self.is_running = False

        self.emit_event("simulation_error", error_info)

        raise error

    def _on_progress_update(self, progress: int, message: str) -> None:
        """
        Handle progress updates from the simulation

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        self.simulation_data["progress"] = progress
        self.emit_event(
            "simulation_progress", {"progress": progress, "message": message}
        )
