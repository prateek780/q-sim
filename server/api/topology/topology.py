import json
import aiofiles # Library for async file operations
from fastapi import APIRouter, HTTPException, Response, Request, status
from typing import Any # For type hinting the request body

# Replace Blueprint with APIRouter
topology_router = APIRouter(
    prefix="/topology", # Matches url_prefix
    tags=["Topology"]   # Optional: For grouping in API docs
)

NETWORK_FILE = "network.json" # Keep the constant

@topology_router.put("/", status_code=status.HTTP_201_CREATED)
async def update_topology(topology_data: Any):
    """
    Receives topology data (expected as JSON in the request body),
    validates basic structure (by virtue of FastAPI parsing it),
    and saves it to the network file asynchronously.

    Returns the saved data.
    """
    # FastAPI automatically parses the JSON request body into `topology_data`
    # based on the type hint (Any, dict, list, or preferably a Pydantic model).

    try:
        # Use json.dumps to convert the received Python object back to a JSON string
        content_to_write = json.dumps(topology_data, indent=4) # Add indent for readability

        # Use aiofiles for async file writing
        async with aiofiles.open(NETWORK_FILE, "w") as f:
            await f.write(content_to_write)

        # Return the data that was successfully processed and saved.
        # FastAPI will automatically serialize this to a JSON response.
        return topology_data

    except TypeError as e:
        # Handle cases where json.dumps fails (e.g., non-serializable data)
        # This might indicate an issue upstream or with the input if not caught by FastAPI/Pydantic
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data provided, cannot serialize to JSON: {e}"
        )
    except Exception as e:
        # Catch potential file writing errors (permissions, disk full, etc.)
        print(f"Error writing topology file: {e}") # Log the error server-side
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save topology data due to a server error."
        )


@topology_router.get("/", response_class=Response) # Specify Response class if returning raw content
async def get_topology():
    """
    Reads the topology data from the network file asynchronously
    and returns its content directly.
    """
    try:
        # Use aiofiles for async file reading
        async with aiofiles.open(NETWORK_FILE, "r") as f:
            content = await f.read()

        # Return the raw file content with appropriate status code and media type
        # Assuming the file contains valid JSON
        return Response(content=content, status_code=status.HTTP_200_OK, media_type="application/json")

    except FileNotFoundError:
        # Replace abort(404) with HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Topology file '{NETWORK_FILE}' not found.")
    except Exception as e:
        # Catch potential file reading errors
        print(f"Error reading topology file: {e}") # Log the error server-side
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read topology data due to a server error."
        )