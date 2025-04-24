import os
import traceback
from fastapi import FastAPI
import uvicorn
from ai_agent.src.orchestration.coordinator import Coordinator
from config.config import load_config
from data.models.connection.redis import get_redis_conn
from server.app import get_app
from fastapi.concurrency import asynccontextmanager
from flask.cli import load_dotenv

load_dotenv()

app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Lifespan: Connecting to Redis...")
    try:
        if get_redis_conn().ping():
            print("Lifespan: Connected to Redis.")
        else:
            raise Exception("Failed to connect to Redis")

    except Exception as e:
        print(f"Lifespan ERROR: Failed to connect to Redis: {e}")

    try:
        # Initialize the Coordinate class
        Coordinator()
        print("Lifespan: Coordinate class initialized.")
    except Exception as e:
        traceback.print_exc()
        print(f"Lifespan ERROR: Failed to initialize Coordinate class: {e}")

    yield
    # Shutdown
    print("Lifespan: Disconnecting from Redis...")
    try:
        redis_conn = get_redis_conn()
        if redis_conn:
            redis_conn.close()
            print("Lifespan: Disconnected from Redis.")
        else:
            print("Lifespan: No Redis connection to close.")
    except Exception as e:
        print(f"Lifespan ERROR: Failed to disconnect from Redis: {e}")

app = get_app(lifespan=lifespan)

if __name__ == '__main__':
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5174"))
    reload_flag = os.getenv("DEBUG", "True").lower() in ["true", "1", "t"]
    
    uvicorn.run(
        "start:app",
        host=host,
        port=port,
        reload=reload_flag
    )