from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any
import yaml
import os
from pathlib import Path

class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: SecretStr
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 60
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    max_tokens: Optional[int] = 1000
    retry_attempts: int = 3

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class AppConfig(BaseSettings):
    llm: LLMConfig
    logging: LoggingConfig
    
    model_config = SettingsConfigDict(env_nested_delimiter='__')
    
    @classmethod
    def from_yaml(cls, file_path: str) -> "AppConfig":
        """Load config from YAML file with environment variable interpolation."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
            
        with open(path, 'r') as f:
            yaml_str = f.read()
            
        # Environment variable substitution
        for key, value in os.environ.items():
            placeholder = f"${{{key}}}"
            if placeholder in yaml_str:
                yaml_str = yaml_str.replace(placeholder, value)
                
        config_dict = yaml.safe_load(yaml_str)
        return cls(**config_dict)

def load_config(config_path: str = "ai_agent/config/llm_config.yaml") -> AppConfig:
    """Load application configuration."""
    return AppConfig.from_yaml(config_path)