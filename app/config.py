from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rapid_secret: str = Field(default="", validation_alias="RAPID_SECRET")
    crawlbase_token: str = Field(default="", validation_alias="CRAWLBASE_TOKEN")
    crawlbase_api_url: str = Field(
        default="https://api.crawlbase.com/",
        validation_alias="CRAWLBASE_API_URL",
    )
    crawlbase_timeout_s: float = Field(default=90.0, validation_alias="CRAWLBASE_TIMEOUT_S")


@lru_cache
def get_settings() -> Settings:
    return Settings()
