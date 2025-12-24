# Development Guide

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Clone the repository
git clone https://github.com/getthevoid/discord-streak.git
cd discord-streak

# Install dependencies
make install

# Copy environment file
cp .env.example .env
# Edit .env with your Discord token and server IDs
```

## Running Locally

```bash
make dev
```

## Available Commands

| Command          | Description                                |
| ---------------- | ------------------------------------------ |
| `make install`   | Install dependencies                       |
| `make dev`       | Run the application                        |
| `make format`    | Format code with ruff                      |
| `make lint`      | Lint code with ruff                        |
| `make typecheck` | Type check with pyright                    |
| `make check`     | Run all checks (format + lint + typecheck) |
| `make test`      | Run tests with pytest                      |
| `make clean`     | Remove cache files                         |

## Project Structure

```
src/
├── __init__.py          # Package metadata
├── __main__.py          # Package entry point
├── main.py              # Application bootstrap
├── engine/
│   └── runner.py        # Discord client and health server
├── models/
│   ├── config.py        # Pydantic settings and server config
│   └── results.py       # Connection state and result models
└── utils/
    ├── errors.py        # Custom exceptions
    └── logger.py        # Colored logging utility

tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
└── integration/         # Integration tests
```

## Code Quality

Before committing, run:

```bash
make check
```

This ensures code is formatted, linted, and type-checked.
