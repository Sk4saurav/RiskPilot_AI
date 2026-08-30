from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./riskpilot.db"
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
