from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_secret_key: str
    supabase_jwks_url: str
    frontend_url: list[str] = ["http://localhost:5173", "https://cleva-connect.vercel.app"]
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()