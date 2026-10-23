"""Configuración central del document-crud-service (pydantic-settings)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Logging
    loglevel: str = "INFO"

    # MongoDB - ÚNICA instancia, base de datos propia
    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db_name: str = "document_crud_db"
    mongo_timeout_ms: int = 5000

    # Auth interna
    internal_api_token: str = "change-me"

    # Límites
    max_text_bytes: int = 15 * 1024 * 1024  # 15 MB (debajo del límite BSON de 16 MB)
    page_size_max: int = 100
    page_size_default: int = 20


settings = Settings()
