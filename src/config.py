import os
import sys
from typing import Final

from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

from src.logger import log
from src.types import Server, Status

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


def get_servers() -> list[Server]:
    servers_str = os.getenv("DISCORD_SERVERS")
    if not servers_str:
        log("error", "DISCORD_SERVERS environment variable not set")
        sys.exit(1)

    servers: list[Server] = []
    for pair in servers_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            log(
                "error", f"Invalid server format: {pair} (expected guild_id:channel_id)"
            )
            sys.exit(1)
        guild_id, channel_id = pair.split(":", 1)
        servers.append(Server(guild_id.strip(), channel_id.strip()))

    if not servers:
        log("error", "No servers configured")
        sys.exit(1)

    return servers
