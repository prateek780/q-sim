"""Redis connection module for network simulation"""
from redis.client import Redis
from redis_om import get_redis_connection

from config.config import load_config

# Global Redis connection
_redis_connection = None

def get_redis_conn(host: str = "localhost", port: int = 6379, db: int = 0) -> Redis:
    """Get or create Redis connection (singleton pattern)"""
    global _redis_connection
    if _redis_connection is None:
        config = load_config()
        redis_config = config.redis
        _redis_connection = Redis(
            host=redis_config.host,
            port=redis_config.port,
            username=redis_config.username,
            password=redis_config.password.get_secret_value(),
            db=redis_config.db,
            decode_responses=True,
        )
        # Configure redis-om to use our connection
        get_redis_connection(client=_redis_connection)
    return _redis_connection