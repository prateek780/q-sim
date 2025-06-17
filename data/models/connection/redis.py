"""Redis connection module for network simulation"""
import os
from redis.client import Redis
from redis_om import get_redis_connection

from config.config import get_config

# Global Redis connection
_redis_connection = None

def get_redis_conn() -> Redis:
    """Get or create Redis connection (singleton pattern)"""
    global _redis_connection
    if _redis_connection is None:
        config = get_config()
        redis_config = config.redis

        _redis_connection = Redis(
            host=redis_config.host,
            port=redis_config.port,
            username=redis_config.username,
            password=redis_config.password.get_secret_value(),
            db=redis_config.db,
            decode_responses=True,
        )
        if _redis_connection.ping():
            pass
        else:
            raise Exception("Failed to connect to Redis")
        # Configure redis-om to use our connection
        redis_url = f"redis://{redis_config.username}:{redis_config.password.get_secret_value()}@{redis_config.host}:{redis_config.port}/{redis_config.db}"
        os.environ["REDIS_OM_URL"] = redis_url
    return _redis_connection