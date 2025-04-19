from typing import Optional
from pydantic import BaseModel, Field, SecretStr


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: SecretStr
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 60
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    max_tokens: Optional[int] = 1000
    retry_attempts: int = 3
