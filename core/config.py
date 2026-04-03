from maxapi import Bot
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
import pathlib

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    db_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/db.sqlite3"
    db_echo: bool = False

    TOKEN: str = os.getenv("TOKEN")

settings = Settings()
bot = Bot(token=settings.TOKEN)