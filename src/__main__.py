import asyncio
import sys

import websockets  # pyright: ignore[reportMissingImports]

from src.client import get_user, keep_online
from src.config import get_status, get_token
from src.logger import log


async def main() -> None:
    token = get_token()
    status = get_status()

    user = await get_user(token)
    if not user:
        log("error", "Invalid token")
        sys.exit(1)

    log("info", f"Logged in as {user['username']} ({user['id']})")
    log("info", f"Status: {status}")

    while True:
        try:
            await keep_online(token, status)
        except websockets.ConnectionClosed:
            log("warn", "Connection closed, reconnecting in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("info", "Shutting down...")
