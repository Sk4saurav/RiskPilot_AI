import os
from pydantic_settings import BaseSettings, SettingsConfigDict

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'riskpilot.db'))

class Settings(BaseSettings):
    api_env: str = "development"
    database_url: str = f"sqlite+aiosqlite:///{DB_PATH}"
    cors_origins: str = "*"
    
    worker_id: str = "worker_default"
    worker_poll_interval: int = 5
    stale_claim_timeout: int = 10
    max_investigation_attempts: int = 3
    
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o"
    openai_api_key: str | None = None
    ipinfo_api_key: str | None = None
    fingerprintjs_api_key: str | None = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
