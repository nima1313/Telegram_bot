from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    bot_token: str = os.getenv("BOT_TOKEN")
    database_url: str = os.getenv("DATABASE_URL")
    redis_url: str = os.getenv("REDIS_URL")
    log_level: str = os.getenv("LOG_LEVEL")

settings = Settings()