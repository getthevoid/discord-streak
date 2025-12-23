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

# Exceptions that trigger reconnection
CONNECTION_ERRORS = (
    websockets.ConnectionClosed,
    websockets.WebSocketException,
    TimeoutError,
    OSError,
    ZombieConnectionError,
    ReconnectRequested,
)


def calculate_backoff(attempt: int) -> float:
    """
    Exponential backoff: 1s -> 2s -> 4s -> 8s -> ... -> 60s (max).
    Jitter prevents multiple clients from reconnecting simultaneously.
    """
    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * JITTER_FACTOR)
    return delay + jitter


def _extract_reconnect_exception(
    eg: ExceptionGroup,  # type: ignore[type-arg]
) -> InvalidSessionError | BaseException | None:
    """Extract the first reconnectable exception from an ExceptionGroup."""
    for exc in eg.exceptions:
        if isinstance(exc, (InvalidSessionError, *CONNECTION_ERRORS)):
            return exc
    return None


async def _handle_reconnect(
    exc: BaseException,
    session: SessionState,
    attempt: int,
) -> int:
    """Handle reconnection logic. Returns updated attempt counter."""
    # Reset backoff after successful connection
    if session.connected:
        attempt = 0

    if isinstance(exc, InvalidSessionError):
        if exc.resumable:
            log("info", "Resumable invalid session, reconnecting...")
            await asyncio.sleep(1)
            return attempt
        session.reset()

    delay = calculate_backoff(attempt)
    log("warn", f"Connection error: {exc}")
    log("info", f"Reconnecting in {delay:.1f}s (attempt {attempt + 1})...")
    await asyncio.sleep(delay)
    return attempt + 1


async def discord_client(
    token: str,
    status: Status,
    servers: list[Server],
) -> None:
    session = SessionState()
    attempt = 0

    while True:
        session.connected = False

        try:
            await keep_online(token, status, servers, session)
        except CONNECTION_ERRORS as e:
            attempt = await _handle_reconnect(e, session, attempt)
        except InvalidSessionError as e:
            attempt = await _handle_reconnect(e, session, attempt)
        except ExceptionGroup as eg:
            exc = _extract_reconnect_exception(eg)
            if exc is None:
                raise
            attempt = await _handle_reconnect(exc, session, attempt)


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
