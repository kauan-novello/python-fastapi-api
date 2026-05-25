from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str = Field(init=False)
    SECRET_KEY: str = Field(init=False)
    ALGORITHM: str = Field(init=False)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(init=False)
    CORS_ORIGINS: str = Field(
        default='http://localhost:3000,http://localhost:5173', init=False
    )
    FRONTEND_URL: str = 'http://localhost:3000'
    EMAIL_FROM: str = 'noreply@example.com'
    SMTP_HOST: str = 'localhost'
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = 'text'
    REDIS_URL: str | None = None
    RATE_LIMIT_BACKEND: str = 'memory'

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as list from comma-separated string."""
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(',')
            if origin.strip()
        ]

    def uses_redis_rate_limit(self) -> bool:
        return self.RATE_LIMIT_BACKEND == 'redis' and bool(self.REDIS_URL)
