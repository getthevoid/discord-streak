"""Core engine for Discord client and server management."""

import asyncio
import json
import random
from http import HTTPStatus
from typing import Final

import httpx
import websockets  # pyright: ignore[reportMissingImports]

from src.models.config import API_URL, GATEWAY_URL, Server, Settings, Status
from src.models.results import SessionState, User
from src.utils.logger import log

# Activity configuration
APP_ID: Final[str] = "1425827351261872219"
ACTIVITY_NAME: Final[str] = "The Void - Discord Activity Streak"
ACTIVITY_DETAILS: Final[str] = "Keep your Discord activity streak alive for 24/7"
ACTIVITY_STATE: Final[str] = "24/7 Online"
REPO_URL: Final[str] = "https://github.com/getthevoid/discord-streak"

# Reconnection settings
BASE_DELAY: Final[float] = 1.0
MAX_DELAY: Final[float] = 60.0
JITTER_FACTOR: Final[float] = 0.1


def generate_client_properties(index: int) -> dict[str, str]:
    """Generate unique client properties for each connection (15 unique combos)."""
    os_list = ["Windows", "Linux", "Mac OS X"]
    browser_list = ["Discord Client", "Chrome", "Firefox", "Safari", "Edge"]

    # All combinations: 3 OS × 5 browsers = 15 unique
    os_name = os_list[index % len(os_list)]
    browser = browser_list[index // len(os_list) % len(browser_list)]

    return {"os": os_name, "browser": browser, "device": ""}


def calculate_backoff(attempt: int) -> float:
    """Exponential backoff: 1s -> 2s -> 4s -> ... -> 60s max."""
    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * JITTER_FACTOR)
    return delay + jitter


class DiscordClient:
    """Discord Gateway WebSocket client."""

    def __init__(self, token: str, status: Status, client_index: int) -> None:
        self.token = token
        self.status = status
        self.client_index = client_index
        self.properties = generate_client_properties(client_index)

    async def get_user(self) -> User | None:
        """Validate token and get user information."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{API_URL}/users/@me",
                headers={"Authorization": self.token},
            )
            if resp.status_code == 200:
                return resp.json()
            return None

    async def keep_online(self, server: Server, session: SessionState) -> None:
        """Maintain connection for a single server."""
        async with websockets.connect(GATEWAY_URL) as ws:
            hello = json.loads(await ws.recv())
            heartbeat_interval: float = hello["d"]["heartbeat_interval"] / 1000

            log(
                "info",
                f"[Server {self.client_index + 1}] Connected to Gateway "
                f"(heartbeat: {heartbeat_interval:.1f}s)",
            )

            # Send identify packet with unique properties
            identify = {
                "op": 2,
                "d": {
                    "token": self.token,
                    "properties": self.properties,
                    "presence": {
                        "status": self.status,
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
            await ws.send(json.dumps(identify))
            await ws.recv()

            # Mark as connected (for backoff reset)
            session.mark_connected()

            # Join voice channel
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
            log(
                "info",
                f"[Server {self.client_index + 1}] Joined voice channel "
                f"{server.channel_id} in guild {server.guild_id}",
            )

            # Simple heartbeat loop
            while True:
                await ws.send(json.dumps({"op": 1, "d": None}))
                await asyncio.sleep(heartbeat_interval)


class HealthServer:
    """HTTP health check server."""

    def __init__(self, port: int = 8080) -> None:
        self.port = port

    async def handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle incoming HTTP request."""
        await reader.readline()
        response = (
            f"HTTP/1.1 {HTTPStatus.OK} OK\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 2\r\n"
            "\r\n"
            "OK"
        )
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def start(self) -> None:
        """Start the health check server."""
        server = await asyncio.start_server(
            self.handle_request,
            "0.0.0.0",
            self.port,  # noqa: S104
        )
        log("info", f"Health server running on port {self.port}")
        async with server:
            await server.serve_forever()


async def run_server_client(
    token: str,
    status: Status,
    server: Server,
    client_index: int,
) -> None:
    """Manage connection for a single server with reconnection."""
    session = SessionState()
    client = DiscordClient(token, status, client_index)
    attempt = 0

    while True:
        session.mark_disconnected()

        try:
            await client.keep_online(server, session)
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
            session.mark_reconnecting()
            await asyncio.sleep(delay)
            attempt += 1


async def run_all(settings: Settings) -> None:
    """Run all server connections and health server."""
    # Create a separate connection for each server
    health_server = HealthServer()
    tasks: list[asyncio.Task[None]] = [asyncio.create_task(health_server.start())]

    for i, server in enumerate(settings.servers):
        task = asyncio.create_task(
            run_server_client(settings.token, settings.status, server, i)
        )
        tasks.append(task)

    await asyncio.gather(*tasks)
