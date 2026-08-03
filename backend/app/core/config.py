from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    anthropic_api_key: str = ""
    openai_api_key: str = ""

    embedding_provider: str = "e5"
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dim: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
