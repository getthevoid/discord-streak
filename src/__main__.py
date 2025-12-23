import asyncio
import random
import sys

import websockets  # pyright: ignore[reportMissingImports]

from src.client import (
    InvalidSessionError,
    ReconnectRequested,
    ZombieConnectionError,
    get_user,
    keep_online,
)
from src.config import get_servers, get_status, get_token
from src.logger import log
from src.server import start_server
from src.types import Server, SessionState, Status

# Reconnection settings
BASE_DELAY = 1.0  # Initial delay in seconds
MAX_DELAY = 60.0  # Maximum delay in seconds
JITTER_FACTOR = 0.1  # Random jitter as percentage of delay


def calculate_backoff(attempt: int) -> float:
    """
    Exponential backoff: 1s -> 2s -> 4s -> 8s -> ... -> 60s (max).
    Jitter prevents multiple clients from reconnecting simultaneously.
    """
    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * JITTER_FACTOR)
    return delay + jitter


async def discord_client(
    token: str,
    status: Status,
    servers: list[Server],
) -> None:
    session = SessionState()
    attempt = 0

    while True:
        # Reset connected flag before each attempt
        session.connected = False

        try:
            await keep_online(token, status, servers, session)
        except (
            websockets.ConnectionClosed,
            websockets.WebSocketException,
            TimeoutError,
            OSError,
            ZombieConnectionError,
            ReconnectRequested,
        ) as e:
            # Reset backoff after successful connection
            if session.connected:
                attempt = 0
            delay = calculate_backoff(attempt)
            log("warn", f"Connection error: {e}")
            log("info", f"Reconnecting in {delay:.1f}s (attempt {attempt + 1})...")
            await asyncio.sleep(delay)
            attempt += 1
        except InvalidSessionError as e:
            if e.resumable:
                # Resumable invalid session - try again quickly
                log("info", "Resumable invalid session, reconnecting...")
                await asyncio.sleep(1)
            else:
                # Non-resumable - session already reset, reconnect with backoff
                if session.connected:
                    attempt = 0
                delay = calculate_backoff(attempt)
                log("info", f"Session invalidated, reconnecting in {delay:.1f}s...")
                await asyncio.sleep(delay)
                attempt += 1
        except ExceptionGroup as eg:
            # Handle TaskGroup exceptions
            handled = False
            for exc in eg.exceptions:
                if isinstance(
                    exc,
                    (
                        websockets.ConnectionClosed,
                        ZombieConnectionError,
                        ReconnectRequested,
                    ),
                ):
                    if session.connected:
                        attempt = 0
                    delay = calculate_backoff(attempt)
                    log("warn", f"Connection error: {exc}")
                    log("info", f"Reconnecting in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    attempt += 1
                    handled = True
                    break
                elif isinstance(exc, InvalidSessionError):
                    if not exc.resumable:
                        session.reset()
                    if session.connected:
                        attempt = 0
                    delay = 1 if exc.resumable else calculate_backoff(attempt)
                    log("info", f"Session issue, reconnecting in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    if not exc.resumable:
                        attempt += 1
                    handled = True
                    break
            if not handled:
                # Unknown exception in group, re-raise
                raise


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
