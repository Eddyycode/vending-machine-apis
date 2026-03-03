"""
config.py — Configuración central con Pydantic BaseSettings.
Lee automáticamente el archivo .env del proyecto.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    app_version: str = "0.1.0"
    secret_key: str = "dev-secret-key-change-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/vending"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Pagos
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # CORS (lista de orígenes separados por coma)
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Retorna una instancia cacheada de Settings.
    Usar como dependencia FastAPI: settings = Depends(get_settings)
    """
    return Settings()


# Instancia global para imports directos
settings = get_settings()
