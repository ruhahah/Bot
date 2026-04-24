from dataclasses import dataclass

from dotenv import load_dotenv
import os

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    google_sheets_id: str


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не задан в .env")
    return Config(
        bot_token=token,
        admin_id=int(os.getenv("ADMIN_ID", "0")),
        google_sheets_id=os.getenv("GOOGLE_SHEETS_ID", ""),
    )
