import asyncio
import random
import sys

import websockets  # pyright: ignore[reportMissingImports]

from src.client import get_user, keep_server_online
from src.config import get_servers, get_status, get_token
from src.logger import log
from src.server import start_server
from src.types import Server, SessionState, Status

# Reconnection settings
BASE_DELAY = 1.0
MAX_DELAY = 60.0
JITTER_FACTOR = 0.1


def calculate_backoff(attempt: int) -> float:
    """Exponential backoff: 1s -> 2s -> 4s -> ... -> 60s max."""
    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * JITTER_FACTOR)
    return delay + jitter


async def server_client(
    token: str,
    status: Status,
    server: Server,
    client_index: int,
) -> None:
    """Manage connection for a single server with reconnection."""
    session = SessionState()
    attempt = 0

    while True:
        session.connected = False

        try:
            await keep_server_online(token, status, server, session, client_index)
        except (
            websockets.ConnectionClosed,
            websockets.WebSocketException,
            OSError,
        ) as e:
            # Reset backoff after successful connection
            if session.connected:
                attempt = 0

            delay = calculate_backoff(attempt)
            error_msg = str(e) or type(e).__name__
            log("warn", f"[Server {client_index + 1}] Connection error: {error_msg}")
            log(
                "info",
                f"[Server {client_index + 1}] Reconnecting in {delay:.1f}s "
                f"(attempt {attempt + 1})...",
            )
            await asyncio.sleep(delay)
            attempt += 1


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

    # Create a separate connection for each server
    tasks = [start_server()]
    for i, server in enumerate(servers):
        tasks.append(server_client(token, status, server, i))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("info", "Shutting down...")
