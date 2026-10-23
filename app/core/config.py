"""Configuración central del document-crud-service (pydantic-settings)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # Logging
    loglevel: str = "INFO"

    # MongoDB (requerido, sin valor por defecto acoplado a Docker)
    mongo_uri: str
    mongo_db_name: str = "document_crud_db"
    mongo_timeout_ms: int = 5000

    # Auth interna (requerido, sin valor por defecto inseguro)
    internal_api_token: str

    # Límites
    max_text_bytes: int = 15 * 1024 * 1024  # 15 MB (debajo del límite BSON de 16 MB)
    page_size_max: int = 100
    page_size_default: int = 20


settings = Settings()
