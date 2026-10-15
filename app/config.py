from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_secret_key: str
    supabase_jwks_url: str
    frontend_url: str = "http://localhost:5173"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 60

    @property
    def cors_origins(self) -> list[str]:
        return [i.strip() for i in self.frontend_url.split(",") if i.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()