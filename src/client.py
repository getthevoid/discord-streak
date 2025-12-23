import asyncio
import json

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


def generate_client_properties(index: int) -> dict[str, str]:
    """Generate unique client properties for each connection (15 unique combos)."""
    os_list = ["Windows", "Linux", "Mac OS X"]
    browser_list = ["Discord Client", "Chrome", "Firefox", "Safari", "Edge"]

    # All combinations: 3 OS × 5 browsers = 15 unique
    os_name = os_list[index % len(os_list)]
    browser = browser_list[index // len(os_list) % len(browser_list)]

    return {"os": os_name, "browser": browser, "device": ""}


async def get_user(token: str) -> User | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_URL}/users/@me",
            headers={"Authorization": token},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


async def keep_server_online(
    token: str,
    status: Status,
    server: Server,
    session: SessionState,
    client_index: int,
) -> None:
    """Maintain connection for a single server."""
    properties = generate_client_properties(client_index)

    async with websockets.connect(GATEWAY_URL) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval: float = hello["d"]["heartbeat_interval"] / 1000

        log(
            "info",
            f"[Server {client_index + 1}] Connected to Gateway "
            f"(heartbeat: {heartbeat_interval:.1f}s)",
        )

        # Send identify packet with unique properties
        identify = {
            "op": 2,
            "d": {
                "token": token,
                "properties": properties,
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
        await ws.send(json.dumps(identify))
        await ws.recv()

        # Mark as connected (for backoff reset)
        session.connected = True

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
            f"[Server {client_index + 1}] Joined voice channel "
            f"{server.channel_id} in guild {server.guild_id}",
        )

        # Simple heartbeat loop
        while True:
            await ws.send(json.dumps({"op": 1, "d": None}))
            await asyncio.sleep(heartbeat_interval)
