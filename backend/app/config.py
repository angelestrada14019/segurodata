"""Configuración del backend — pydantic-settings, todo desde variables de entorno."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["development", "test", "production"] = "development"
    auth_mode: Literal["enabled", "disabled"] = "enabled"

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwks_url: str = ""  # escape hatch si el proyecto usa llaves asimétricas

    openrouter_api_key: str = ""
    llm_model: str = "google/gemini-flash-1.5"
    llm_model_fallback: str = "anthropic/claude-haiku"
    llm_max_tokens: int = 600
    llm_cache_ttl_seconds: int = 86_400
    llm_cache_maxsize: int = 256

    embeddings_backend: Literal["sentence-transformers", "fastembed"] = "sentence-transformers"
    embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    cors_origins: str = "http://localhost:5173"
    tabla_ontologica_path: str = ""  # override del JSON bundleado (Notebook 03)

    rate_limit_default: str = "60/minute"
    rate_limit_llm: str = "10/minute"

    @field_validator("auth_mode")
    @classmethod
    def _norm(cls, v: str) -> str:
        return v.lower()

    @model_validator(mode="after")
    def _auth_disabled_solo_en_dev(self) -> "Settings":
        # AUTH_MODE=disabled jamás en producción — guard del contrato (skill backend-segurodata)
        if self.auth_mode == "disabled" and self.env == "production":
            raise ValueError("AUTH_MODE=disabled está prohibido con ENV=production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
