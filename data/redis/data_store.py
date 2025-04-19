from enum import Enum
import redis
from config.config import load_config
from utils.singleton import singleton


class RedisPrefix(Enum):
    SIMULATION = "simulation"
    NETWORK = "network"


@singleton
class DataStore:
    def __init__(self):
        config = load_config()
        self.redis_config = config.redis

    def connect_redis(self):
        self.client = redis.Redis(
            host=self.redis_config.host,
            port=self.redis_config.port,
            username=self.redis_config.username,
            password=self.redis_config.password.get_secret_value(),
            db=self.redis_config.db,
            decode_responses=True,
        )

        self.client.ping()

        print("Connected to Redis")

    def check_connection(self):
        # Check if the Redis server is running
        try:
            self.client.ping()
            return True
        except redis.ConnectionError:
            return False

    def save_simulation(self, simulation_id, data):
        # Save simulation data to Redis
        self.client.set(simulation_id, data)

    def list_simulations(self):
        # List all simulation IDs
        return self.client.keys(f"{RedisPrefix.SIMULATION.value}:*")
