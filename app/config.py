from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rapid_secret: str = Field(default="", validation_alias="RAPID_SECRET")
    playwright_headless: bool = True
    scrape_timeout_ms: int = 30_000
    max_concurrent_pages: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
