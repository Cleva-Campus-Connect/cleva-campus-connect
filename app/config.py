from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_secret_key: str
    supabase_jwks_url: str
    frontend_url: list[str] = ["http://localhost:5173"]
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 60

    @field_validator("frontend_url", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()