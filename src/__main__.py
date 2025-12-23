import asyncio
import sys

import websockets  # pyright: ignore[reportMissingImports]

from src.client import get_user, keep_online
from src.config import get_servers, get_status, get_token
from src.logger import log
from src.server import start_server
from src.types import Server, Status


async def discord_client(
    token: str,
    status: Status,
    servers: list[Server],
) -> None:
    while True:
        try:
            await keep_online(token, status, servers)
        except websockets.ConnectionClosed:
            log("warn", "Connection closed, reconnecting in 5s...")
            await asyncio.sleep(5)


async def main() -> None:
    token = get_token()
    status = get_status()
    servers = get_servers()

    user = await get_user(token)
    if not user:
        log("error", "Invalid token")
        sys.exit(1)

    log("info", f"Logged in as {user['username']} ({user['id']})")
    log("info", f"Status: {status}")
    log("info", f"Servers: {len(servers)}")

    await asyncio.gather(
        start_server(),
        discord_client(token, status, servers),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("info", "Shutting down...")
