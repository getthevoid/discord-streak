# discord-streak

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Keep your Discord activity streak alive 24/7.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/getthevoid/discord-streak.git
cd discord-streak
cp .env.example .env

# Configure .env with your token and servers
# DISCORD_TOKEN=your_token
# DISCORD_SERVERS=guild_id:channel_id

# Run
make dev
```

## Features

- **24/7 Online Presence** — Maintains your Discord status around the clock
- **Multi-Server Support** — Join voice channels across up to 15 servers simultaneously
- **Auto-Reconnect** — Handles disconnects with exponential backoff (1s → 60s max)
- **Configurable Status** — Choose between online, idle, or dnd
- **Free Hosting Ready** — Built-in health server for Render/Railway

## Configuration

| Variable          | Description                                   | Default  |
| ----------------- | --------------------------------------------- | -------- |
| `DISCORD_TOKEN`   | Your Discord user token                       | Required |
| `DISCORD_STATUS`  | Status: `online`, `idle`, `dnd`               | `online` |
| `DISCORD_SERVERS` | `guild_id:channel_id` pairs (comma-separated) | Required |

## Documentation

- [Deployment Guide](docs/deployment.md) — Deploy to Render, Railway, or Docker
- [Development Guide](docs/development.md) — Local setup and contributing

## Metadata

```python
__metadata__ = {
    "name": "discord-streak",
    "version": "1.1.1",
    "author": "getthevoid",
    "license": "MIT",
    "python": ">=3.12",
    "repository": "github.com/getthevoid/discord-streak",
}
```

## Disclaimer

> This tool uses a user token which is against Discord's Terms of Service. Use at your own risk.
