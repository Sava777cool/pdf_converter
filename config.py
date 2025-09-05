from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    OPENAI_API_KEY: str

    class Config:
        env_file = BASE_DIR / "config/.env"


settings = Settings()
