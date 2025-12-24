# Deployment Guide

Deploy discord-streak to run 24/7 on various platforms.

## Render (Free Tier)

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Configure the service:
   - **Build Command:** `uv sync --frozen --no-dev --compile-bytecode && uv cache prune --ci`
   - **Start Command:** `uv run --no-dev python -m src`
4. Add environment variables in the dashboard
5. Configure **Build Filters** (optional):
   - **Included Paths:** `src/**`, `pyproject.toml`, `uv.lock`
6. Deploy

> **Note:** Set up [UptimeRobot](https://uptimerobot.com) to ping your Render URL every 5 minutes to prevent the free tier from sleeping.

## Docker (Local)

Run locally with Docker Compose:

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start container (detached)
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down
```

> **Note:** Running locally requires your PC to be on 24/7. For true 24/7 uptime, use Render or Railway instead.

## Environment Variables

All deployment methods require these environment variables:

| Variable          | Description                                          | Required               |
| ----------------- | ---------------------------------------------------- | ---------------------- |
| `DISCORD_TOKEN`   | Your Discord user token                              | Yes                    |
| `DISCORD_STATUS`  | Status: `online`, `idle`, or `dnd`                   | No (default: `online`) |
| `DISCORD_SERVERS` | Comma-separated `guild_id:channel_id` pairs (max 15) | Yes                    |

**Example:**

```env
DISCORD_TOKEN=your_token_here
DISCORD_STATUS=dnd
DISCORD_SERVERS=123456789:987654321,111111111:222222222
```
