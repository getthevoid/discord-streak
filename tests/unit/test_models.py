"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.models.config import Server, Settings
from src.models.results import ConnectionResult, ConnectionState, SessionState


class TestServer:
    """Tests for Server model."""

    def test_valid_server(self) -> None:
        """Test creating a valid server."""
        server = Server(guild_id="123456789", channel_id="987654321")
        assert server.guild_id == "123456789"
        assert server.channel_id == "987654321"

    def test_invalid_guild_id(self) -> None:
        """Test that non-numeric guild_id raises error."""
        with pytest.raises(ValidationError):
            Server(guild_id="invalid", channel_id="123456789")

    def test_invalid_channel_id(self) -> None:
        """Test that non-numeric channel_id raises error."""
        with pytest.raises(ValidationError):
            Server(guild_id="123456789", channel_id="invalid")

    def test_empty_guild_id(self) -> None:
        """Test that empty guild_id raises error."""
        with pytest.raises(ValidationError):
            Server(guild_id="", channel_id="123456789")


class TestSettings:
    """Tests for Settings model."""

    def test_settings_from_env(self, mock_env: dict[str, str]) -> None:
        """Test loading settings from environment variables."""
        settings = Settings()  # pyright: ignore[reportCallIssue]
        assert settings.token == "test_token_12345"
        assert settings.status == "online"
        assert len(settings.servers) == 2

    def test_servers_parsing(self, sample_settings: Settings) -> None:
        """Test parsing of servers from environment."""
        servers = sample_settings.servers
        assert len(servers) == 2
        assert servers[0].guild_id == "123456789"
        assert servers[0].channel_id == "987654321"
        assert servers[1].guild_id == "111111111"
        assert servers[1].channel_id == "222222222"

    def test_default_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default status value."""
        # Clear any existing .env file influence by setting env vars directly
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("DISCORD_SERVERS", "123:456")
        monkeypatch.delenv("DISCORD_STATUS", raising=False)

        # Create settings without env file to test default
        from pydantic_settings import SettingsConfigDict

        class TestSettings(Settings):
            model_config = SettingsConfigDict(
                env_prefix="DISCORD_",
                env_file=None,  # Disable .env file
            )

        settings = TestSettings()  # pyright: ignore[reportCallIssue]
        assert settings.status == "online"


class TestSessionState:
    """Tests for SessionState model."""

    def test_initial_state(self) -> None:
        """Test initial session state."""
        session = SessionState()
        assert session.connected is False
        assert session.state == ConnectionState.DISCONNECTED
        assert session.last_connected is None
        assert session.reconnect_attempts == 0

    def test_mark_connected(self) -> None:
        """Test marking session as connected."""
        session = SessionState()
        session.mark_connected()
        assert session.connected is True
        assert session.state == ConnectionState.CONNECTED
        assert session.last_connected is not None
        assert session.reconnect_attempts == 0

    def test_mark_disconnected(self) -> None:
        """Test marking session as disconnected."""
        session = SessionState()
        session.mark_connected()
        session.mark_disconnected()
        assert session.connected is False
        assert session.state == ConnectionState.DISCONNECTED

    def test_mark_reconnecting(self) -> None:
        """Test marking session as reconnecting."""
        session = SessionState()
        session.mark_reconnecting()
        assert session.state == ConnectionState.RECONNECTING
        assert session.reconnect_attempts == 1
        session.mark_reconnecting()
        assert session.reconnect_attempts == 2


class TestConnectionResult:
    """Tests for ConnectionResult model."""

    def test_success_result(self) -> None:
        """Test creating a successful connection result."""
        result = ConnectionResult.success_result(server_index=0)
        assert result.success is True
        assert result.error_message is None
        assert result.server_index == 0

    def test_failure_result(self) -> None:
        """Test creating a failed connection result."""
        result = ConnectionResult.failure_result(
            server_index=1, error="Connection timeout", attempts=3
        )
        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert result.attempt_count == 3
        assert result.server_index == 1
