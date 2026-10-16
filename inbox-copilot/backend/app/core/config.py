from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    secret_key: str = "change-me"

    database_url: str = "postgresql+psycopg://copilot:copilot@localhost:5432/copilot"
    redis_url: str = "redis://localhost:6379/0"

    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    classification_confidence_threshold: float = 0.7


settings = Settings()