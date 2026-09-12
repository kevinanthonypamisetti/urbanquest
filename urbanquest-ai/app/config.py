from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UrbanQuest AI"
    maps_provider: str = "demo"
    google_maps_api_key: Optional[str] = None
    max_candidates: int = 8
    cors_origins: str = "http://localhost:5173"
    database_url: Optional[str] = None
    environment: str = "development"
    development_otp: str = "123456"
    session_days: int = 30
    google_oauth_url: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    frontend_url: str = "http://localhost:5173"
    resend_api_key: Optional[str] = None
    auth_from_email: str = "UrbanQuest <onboarding@resend.dev>"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
