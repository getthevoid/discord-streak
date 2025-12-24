"""Shared test fixtures."""

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest

from src.models.config import Server, Settings


@pytest.fixture
def mock_env() -> Generator[dict[str, str], Any, None]:
    """Provide mock environment variables."""
    env = {
        "DISCORD_TOKEN": "test_token_12345",
        "DISCORD_STATUS": "online",
        "DISCORD_SERVERS": "123456789:987654321,111111111:222222222",
    }
    with patch.dict("os.environ", env, clear=False):
        yield env


@pytest.fixture
def sample_server() -> Server:
    """Provide a sample server configuration."""
    return Server(guild_id="123456789", channel_id="987654321")


@pytest.fixture
def sample_settings(mock_env: dict[str, str]) -> Settings:
    """Provide sample settings loaded from mock environment."""
    return Settings()  # pyright: ignore[reportCallIssue]
