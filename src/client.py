import asyncio
import json
import time
from typing import Any

import httpx  # pyright: ignore[reportMissingImports]
import websockets  # pyright: ignore[reportMissingImports]

from src.config import API_URL, GATEWAY_URL
from src.logger import log
from src.types import Server, SessionState, Status, User

# Activity
APP_ID = "1425827351261872219"
ACTIVITY_NAME = "The Void - Discord Activity Streak"
ACTIVITY_DETAILS = "Keep your Discord activity streak alive for 24/7"
ACTIVITY_STATE = "24/7 Online"
REPO_URL = "https://github.com/getthevoid/discord-streak"

# Connection settings
CONNECT_TIMEOUT = 30.0
CLOSE_TIMEOUT = 10.0

# Discord Gateway Opcodes
OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_RESUME = 6
OP_RECONNECT = 7
OP_INVALID_SESSION = 9
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11


class ZombieConnectionError(Exception):
    """Raised when heartbeat ACK is not received."""

    pass


class ReconnectRequested(Exception):
    """Raised when Discord requests a reconnect (op 7)."""

    pass


class InvalidSessionError(Exception):
    """Raised when session is invalid (op 9)."""

    def __init__(self, resumable: bool) -> None:
        self.resumable = resumable
        super().__init__(f"Invalid session (resumable={resumable})")


async def get_user(token: str) -> User | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_URL}/users/@me",
            headers={"Authorization": token},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


def _build_identify_payload(token: str, status: Status) -> dict[str, Any]:
    """Build the identify payload for initial connection."""
    return {
        "op": OP_IDENTIFY,
        "d": {
            "token": token,
            "properties": {
                "os": "Windows",
                "browser": "Chrome",
                "device": "",
            },
            "presence": {
                "status": status,
                "since": 0,
                "activities": [
                    {
                        "name": ACTIVITY_NAME,
                        "type": 0,
                        "application_id": APP_ID,
                        "details": ACTIVITY_DETAILS,
                        "state": ACTIVITY_STATE,
                        "buttons": ["GitHub Repository"],
                        "metadata": {"button_urls": [REPO_URL]},
                    }
                ],
                "afk": False,
            },
        },
    }


def _build_resume_payload(token: str, session: SessionState) -> dict[str, Any]:
    """Build the resume payload for reconnection."""
    return {
        "op": OP_RESUME,
        "d": {
            "token": token,
            "session_id": session.session_id,
            "seq": session.sequence,
        },
    }


async def _send_heartbeat(
    ws: Any,
    session: SessionState,
) -> None:
    """Send a heartbeat and check for zombie connection."""
    if not session.last_heartbeat_acked:
        raise ZombieConnectionError("No heartbeat ACK received, connection is zombie")

    session.last_heartbeat_acked = False
    await ws.send(json.dumps({"op": OP_HEARTBEAT, "d": session.sequence}))


async def _heartbeat_loop(
    ws: Any,
    interval: float,
    session: SessionState,
) -> None:
    """Continuously send heartbeats at the specified interval."""
    while True:
        await asyncio.sleep(interval)
        await _send_heartbeat(ws, session)


async def _handle_dispatch(
    ws: Any,
    event: str | None,
    data: dict[str, Any],
    session: SessionState,
    servers: list[Server],
) -> None:
    """Handle dispatch events (op 0)."""
    if event == "READY":
        session.session_id = data["session_id"]
        session.resume_gateway_url = data.get("resume_gateway_url")
        session.connected = True
        sid = session.session_id
        log("info", f"Session established: {sid[:8] if sid else 'unknown'}...")

        # Join voice channels on READY (debounce: 60s cooldown)
        now = time.time()
        if now - session.last_voice_join > 60:
            session.last_voice_join = now
            for server in servers:
                await _join_voice_channel(ws, server)

    elif event == "RESUMED":
        session.connected = True
        log("info", "Session resumed successfully")


async def _handle_message(
    ws: Any,
    data: dict[str, Any],
    session: SessionState,
    servers: list[Server],
) -> None:
    """Handle incoming Gateway messages."""
    op = data.get("op")
    s = data.get("s")

    if s is not None:
        session.sequence = s

    if op == OP_DISPATCH:
        d = data.get("d")
        if d is not None:
            await _handle_dispatch(ws, data.get("t"), d, session, servers)

    elif op == OP_HEARTBEAT:
        await ws.send(json.dumps({"op": OP_HEARTBEAT, "d": session.sequence}))

    elif op == OP_RECONNECT:
        log("warn", "Discord requested reconnect")
        raise ReconnectRequested()

    elif op == OP_INVALID_SESSION:
        resumable = data.get("d") is True
        log("warn", f"Invalid session (resumable={resumable})")
        if not resumable:
            session.reset()
        raise InvalidSessionError(resumable)

    elif op == OP_HEARTBEAT_ACK:
        session.last_heartbeat_acked = True


async def _message_receiver(
    ws: Any,
    session: SessionState,
    servers: list[Server],
) -> None:
    """Receive and handle incoming messages."""
    async for message in ws:
        data = json.loads(message)
        await _handle_message(ws, data, session, servers)


async def _join_voice_channel(
    ws: Any,
    server: Server,
) -> None:
    """Join a voice channel."""
    voice_state = {
        "op": 4,
        "d": {
            "guild_id": server.guild_id,
            "channel_id": server.channel_id,
            "self_mute": True,
            "self_deaf": True,
        },
    }
    await ws.send(json.dumps(voice_state))
    log("info", f"Joined voice channel {server.channel_id} in guild {server.guild_id}")


async def keep_online(
    token: str,
    status: Status,
    servers: list[Server],
    session: SessionState,
) -> None:
    """
    Maintain connection to Discord Gateway.

    Args:
        token: Discord user token
        status: Online status (online/idle/dnd)
        servers: List of servers with voice channels to join
        session: Session state for tracking resumption data
    """
    gateway_url = session.resume_gateway_url or GATEWAY_URL
    if session.resume_gateway_url and "?" not in gateway_url:
        gateway_url += "?v=10&encoding=json"

    async with asyncio.timeout(CONNECT_TIMEOUT):
        async with websockets.connect(
            gateway_url,
            close_timeout=CLOSE_TIMEOUT,
        ) as ws:
            # Receive HELLO
            hello = json.loads(await ws.recv())
            if hello.get("op") != OP_HELLO:
                raise RuntimeError(f"Expected HELLO, got op={hello.get('op')}")

            heartbeat_interval: float = hello["d"]["heartbeat_interval"] / 1000
            log("info", f"Connected to Gateway (heartbeat: {heartbeat_interval:.1f}s)")

            # Reset heartbeat ACK state for new connection
            session.last_heartbeat_acked = True

            # Send identify or resume
            if session.can_resume():
                log("info", "Attempting session resume...")
                await ws.send(json.dumps(_build_resume_payload(token, session)))
            else:
                await ws.send(json.dumps(_build_identify_payload(token, status)))
                # Wait for READY response
                ready = json.loads(await ws.recv())
                await _handle_message(ws, ready, session, servers)

            # Run heartbeat and message receiver concurrently
            async with asyncio.TaskGroup() as tg:
                tg.create_task(_heartbeat_loop(ws, heartbeat_interval, session))
                tg.create_task(_message_receiver(ws, session, servers))
