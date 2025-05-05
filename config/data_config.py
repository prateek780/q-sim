from pydantic import BaseModel, Field, SecretStr

class RedisConfig(BaseModel):
    host: str = 'localhost'
    port: int = 6379
    username: str = 'default'
    password: SecretStr 
    db: int = 0
    ssl: bool = True
    connection_timeout: int = 10