import asyncio
import json
import os
import sys

import httpx
import websockets
from dotenv import load_dotenv

load_dotenv()

GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
API_URL = "https://discord.com/api/v10"


async def keep_online(token: str, status: str = "online") -> None:
    async with websockets.connect(GATEWAY_URL) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000

        identify = {
            "op": 2,
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
                    "activities": [],
                    "afk": False,
                },
            },
        }
        await ws.send(json.dumps(identify))

        while True:
            await ws.send(json.dumps({"op": 1, "d": None}))
            await asyncio.sleep(heartbeat_interval)


async def get_user(token: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_URL}/users/@me",
            headers={"Authorization": token},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        sys.exit(1)

    status = os.getenv("DISCORD_STATUS", "online")
    if status not in ("online", "idle", "dnd"):
        print("Error: DISCORD_STATUS must be one of: online, idle, dnd")
        sys.exit(1)

    user = await get_user(token)
    if not user:
        print("Error: Invalid token")
        sys.exit(1)

    print(f"Logged in as {user['username']} ({user['id']})")
    print(f"Status: {status}")

    while True:
        try:
            await keep_online(token, status)
        except websockets.ConnectionClosed:
            print("Connection closed, reconnecting...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
