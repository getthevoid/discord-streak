import asyncio
import json
import os
import sys
from datetime import datetime

import httpx
import websockets
from colorama import Fore, Style, init
from dotenv import load_dotenv

init()
load_dotenv()

GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
API_URL = "https://discord.com/api/v10"

LEVEL_COLORS = {
    "info": Fore.CYAN,
    "warn": Fore.YELLOW,
    "error": Fore.RED,
}


def log(level: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = LEVEL_COLORS.get(level, Fore.WHITE)
    print(
        f"{Fore.WHITE}[{timestamp}] {color}[{level.upper()}]{Style.RESET_ALL} {message}"
    )


async def keep_online(token: str, status: str = "online") -> None:
    async with websockets.connect(GATEWAY_URL) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000

        log("info", f"Connected to Gateway (heartbeat: {heartbeat_interval:.1f}s)")

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
        log("error", "DISCORD_TOKEN environment variable not set")
        sys.exit(1)

    status = os.getenv("DISCORD_STATUS", "online")
    if status not in ("online", "idle", "dnd"):
        log("error", "DISCORD_STATUS must be one of: online, idle, dnd")
        sys.exit(1)

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
