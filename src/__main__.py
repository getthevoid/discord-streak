import asyncio
import sys

import websockets  # pyright: ignore[reportMissingImports]

from src.client import get_user, keep_online
from src.config import get_channel_id, get_guild_id, get_status, get_token
from src.logger import log
from src.server import start_server
from src.types import Status


async def discord_client(
    token: str,
    status: Status,
    guild_id: str,
    channel_id: str,
) -> None:
    while True:
        try:
            await keep_online(token, status, guild_id, channel_id)
        except websockets.ConnectionClosed:
            log("warn", "Connection closed, reconnecting in 5s...")
            await asyncio.sleep(5)


async def main() -> None:
    token = get_token()
    status = get_status()
    guild_id = get_guild_id()
    channel_id = get_channel_id()

    user = await get_user(token)
    if not user:
        log("error", "Invalid token")
        sys.exit(1)

    log("info", f"Logged in as {user['username']} ({user['id']})")
    log("info", f"Status: {status}")

    await asyncio.gather(
        start_server(),
        discord_client(token, status, guild_id, channel_id),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("info", "Shutting down...")
