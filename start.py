import os
from fastapi import FastAPI
import uvicorn
from server.app import get_app
from data.redis.data_store import DataStore
from fastapi.concurrency import asynccontextmanager
from flask.cli import load_dotenv

load_dotenv()

app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Lifespan: Connecting to Redis...")
    ds = DataStore()
    try:
        ds.connect_redis() # Make async and await if possible
        print("Lifespan: Connected to Redis.")
        app.state.data_store = ds # Optional: store on app state
    except Exception as e:
        print(f"Lifespan ERROR: Failed to connect to Redis: {e}")
        # Decide how to handle connection failure
    yield
    # Shutdown
    print("Lifespan: Disconnecting from Redis...")
    try:
        if hasattr(ds, 'disconnect_redis'):
            ds.disconnect_redis() # Make async and await if possible
            print("Lifespan: Disconnected from Redis.")
    except Exception as e:
        print(f"Lifespan ERROR: Failed to disconnect from Redis: {e}")

app = get_app(lifespan=lifespan)

if __name__ == '__main__':
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5174"))
    reload_flag = os.getenv("DEBUG", "True").lower() in ["true", "1", "t"]
    
    uvicorn.run(
        "start:app", # Point uvicorn to the app instance in this file
        host=host,
        port=port,
        reload=reload_flag
    )