import json
from fastapi import APIRouter, HTTPException, Response, status, Body
from typing import Dict, Any # For type hints

# Assuming SimulationManager is defined elsewhere and has appropriate methods
from data.models.topology.world_model import get_topology_from_redis
from server.api.simulation.manager import SimulationManager # Keep this import

# Replace Blueprint with APIRouter
simulation_router = APIRouter(
    prefix="/simulation", # Matches url_prefix
    tags=["Simulation"]   # Optional: For grouping in API docs
)

# --- Get Singleton Instance ---
# This part likely remains the same, assuming get_instance works as intended
try:
    manager = SimulationManager.get_instance()
except Exception as e:
    # Handle potential errors during manager initialization if necessary
    print(f"CRITICAL: Failed to initialize SimulationManager: {e}")
    # Depending on your app's requirements, you might want to exit
    # or have the endpoints raise a 503 Service Unavailable.
    # For now, we'll let it potentially fail later if manager is None.
    manager = None # Or handle more gracefully

# --- Route Definitions ---

@simulation_router.get(
    '/status/',
    summary="Get current simulation status" # Optional: For docs
)
async def get_simulation_status():
    """
    Returns whether the simulation managed by the SimulationManager is currently running.
    """
    if manager is None:
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Simulation Manager not initialized")
    # FastAPI automatically converts dict to JSON response with status 200 OK
    return {
        'is_running': manager.is_running
    }

@simulation_router.post(
    '/message/',
    status_code=status.HTTP_200_OK, # Explicitly set success status
    summary="Send a message/command to the running simulation"
)
async def send_simulation_message(
    # Use Body(...) to explicitly indicate data comes from request body.
    # Use Dict[str, Any] or a more specific Pydantic model if you know the structure.
    message_data: Dict[str, Any] = Body(...)
):
    """
    Sends a command (provided as JSON in the request body)
    to the simulation via the SimulationManager.
    Requires the simulation to be running.
    """
    if manager is None:
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Simulation Manager not initialized")

    if not manager.is_running:
        # Use HTTPException for errors - more standard in FastAPI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation Not Running"
        )

    try:
        # Consider if send_message_command should be async
        # If it's potentially blocking (I/O, long computation), make it async
        # await manager.send_message_command(**message_data)
        manager.send_message_command(**message_data) # Assuming sync for now

        # Return a success message (JSON is idiomatic in FastAPI)
        return {"message": "Message command sent"}
        # If plain text is strictly needed:
        # return Response(content="Message command sent", status_code=status.HTTP_200_OK, media_type="text/plain")
    except TypeError as e:
         # Handle cases where data doesn't match expected args for send_message_command
         raise HTTPException(
              status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # Good status for invalid data structure
              detail=f"Invalid message data format: {e}"
         )
    except Exception as e:
        # Catch other potential errors from the manager
        print(f"Error sending simulation message: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@simulation_router.delete(
    "/",
    summary="Stop the currently running simulation"
)
async def stop_simulation():
    """
    Stops the simulation if it is currently running.
    """
    if manager is None:
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Simulation Manager not initialized")

    if not manager.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation not running"
        )

    try:
        # Consider if stop should be async (await manager.stop())
        manager.stop() # Assuming sync for now
        return {"message": "Simulation Stopped"}
        # If plain text is strictly needed:
        # return Response(content="Simulation Stopped", status_code=status.HTTP_200_OK, media_type="text/plain")
    except Exception as e:
        # Catch potential errors during stop
        print(f"Error stopping simulation: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop simulation: {str(e)}"
        )


# Handle both GET and POST for starting the simulation
@simulation_router.api_route(
    "/{topology_id}",
    methods=["GET", "POST"], # Specify allowed methods
    status_code=status.HTTP_201_CREATED, # Success status code
    summary="Start the simulation using the network file",
    responses={ # Define possible responses for documentation
        status.HTTP_409_CONFLICT: {"description": "Simulation already running"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Error during simulation start"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Simulation Manager not initialized"}
    }
)
async def execute_simulation(topology_id:str):
    """
    Starts the simulation using the predefined 'network.json' file.
    Returns 201 Created on success.
    Returns 409 Conflict if the simulation is already running.
    Returns 500 Internal Server Error if starting fails.
    Accessible via both GET and POST requests.
    """
    if manager is None:
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Simulation Manager not initialized")
    
    world = get_topology_from_redis(topology_id)

    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topology with ID '{topology_id}' not found."
        )

    try:
        simulation_started = manager.start_simulation(world)

        if not simulation_started:
            # Use HTTPException for conflict
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Simulation already running"
            )

        # On success (201 Created is set by the decorator)
        return {"message": "Simulation started"}

    except FileNotFoundError:
         # If start_simulation can raise this specifically
         raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail=f"Network file '{network_file}' not found."
         )
    except Exception as e:
        # Catch other potential errors during start
        print(f"Error starting simulation: {e}") # Log the error
        # Use HTTPException for server errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting simulation: {str(e)}"
        )
