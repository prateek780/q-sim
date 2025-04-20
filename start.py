import os
from fastapi import FastAPI
import uvicorn
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
        # Decide how to handle connection failure
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