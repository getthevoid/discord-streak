import os
import sys
from typing import Final

from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

from src.logger import log
from src.types import Status

load_dotenv()

GATEWAY_URL: Final[str] = "wss://gateway.discord.gg/?v=10&encoding=json"
API_URL: Final[str] = "https://discord.com/api/v10"


def get_token() -> str:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        log("error", "DISCORD_TOKEN environment variable not set")
        sys.exit(1)
    return token


def get_status() -> Status:
    status = os.getenv("DISCORD_STATUS", "online")
    if status not in ("online", "idle", "dnd"):
        log("error", "DISCORD_STATUS must be one of: online, idle, dnd")
        sys.exit(1)
    return status
