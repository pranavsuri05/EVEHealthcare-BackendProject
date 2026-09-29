from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "EVE Healthcare Booking Service"
    app_env: str = "development"
    debug: bool = True

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
