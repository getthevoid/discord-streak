# discord-streak

Keep your Discord activity streak alive by maintaining online presence.

## What is this?

Discord tracks activity streaks - consecutive days of messaging in servers. This tool keeps your Discord account online 24/7 to help maintain your activity streak and show your presence to friends.

## Features

- Maintains online status via Discord Gateway
- Joins voice channel to maintain activity
- Configurable status (online, idle, dnd)
- Auto-reconnect on connection drops
- Lightweight and minimal dependencies

## Setup

1. Clone the repository
2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy `.env.example` to `.env` and add your Discord token:

   ```bash
   cp .env.example .env
   ```

4. Run:

   ```bash
   make dev
   ```

## Configuration

| Variable             | Description                           | Default  |
| -------------------- | ------------------------------------- | -------- |
| `DISCORD_TOKEN`      | Your Discord user token               | Required |
| `DISCORD_STATUS`     | Status to display (online, idle, dnd) | `online` |
| `DISCORD_GUILD_ID`   | Server ID to join voice channel       | Required |
| `DISCORD_CHANNEL_ID` | Voice channel ID to join              | Required |

## Development

```bash
make install    # Install dependencies
make dev        # Run the application
make format     # Format code with ruff
make lint       # Lint code with ruff
make typecheck  # Type check with pyright
make check      # Run all checks
make clean      # Remove cache files
```

## Disclaimer

This tool uses a user token which is against Discord's Terms of Service. Use at your own risk.
