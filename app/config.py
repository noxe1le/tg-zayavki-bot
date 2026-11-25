from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_id: int | None = Field(default=None, alias="ADMIN_ID")
    db_path: str = Field(default="zayavki.db", alias="DB_PATH")
    throttle_rate: float = Field(default=0.7, alias="THROTTLE_RATE")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
