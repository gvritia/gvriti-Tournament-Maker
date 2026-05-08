from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tournament Maker Backend"
    environment: str = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tournament_maker"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/tournament_maker"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        non_production_environments = {"local", "test", "development"}
        if (
            self.environment.lower() not in non_production_environments
            and self.secret_key == "change-me-in-production"
        ):
            raise ValueError("SECRET_KEY must be changed outside local environments.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
