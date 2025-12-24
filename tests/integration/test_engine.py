"""Integration tests for engine components."""

import asyncio
import contextlib
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.engine.runner import DiscordClient, HealthServer, calculate_backoff


class TestHealthServer:
    """Tests for HealthServer."""

    @pytest.fixture
    def health_server(self) -> HealthServer:
        """Create a health server instance."""
        return HealthServer(port=8081)

    async def test_health_server_responds(self, health_server: HealthServer) -> None:
        """Test that health server responds with OK."""
        # Start server in background
        server_task = asyncio.create_task(health_server.start())

        # Wait for server to start
        await asyncio.sleep(0.1)

        try:
            # Connect and send request
            reader, writer = await asyncio.open_connection("127.0.0.1", 8081)
            writer.write(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await writer.drain()

            response = await reader.read(1024)
            assert b"200 OK" in response
            assert b"OK" in response

            writer.close()
            await writer.wait_closed()
        finally:
            server_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await server_task


class TestDiscordClient:
    """Tests for DiscordClient."""

    def test_client_initialization(self) -> None:
        """Test client initialization."""
        client = DiscordClient(token="test_token", status="online", client_index=0)
        assert client.token == "test_token"
        assert client.status == "online"
        assert client.client_index == 0
        assert "os" in client.properties
        assert "browser" in client.properties

    async def test_get_user_success(self) -> None:
        """Test successful user fetch."""
        client = DiscordClient(token="test_token", status="online", client_index=0)

        with patch("src.engine.runner.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            # Response is not async, only get() is async
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "123", "username": "testuser"}
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            user = await client.get_user()
            assert user is not None
            assert user["id"] == "123"
            assert user["username"] == "testuser"

    async def test_get_user_failure(self) -> None:
        """Test failed user fetch (invalid token)."""
        client = DiscordClient(token="invalid_token", status="online", client_index=0)

        with patch("src.engine.runner.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 401
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            user = await client.get_user()
            assert user is None


class TestBackoff:
    """Tests for backoff calculation."""

    def test_initial_backoff(self) -> None:
        """Test initial backoff delay."""
        delay = calculate_backoff(0)
        assert 1.0 <= delay <= 1.1  # 1s + up to 10% jitter

    def test_exponential_increase(self) -> None:
        """Test exponential backoff increase."""
        delay_1 = calculate_backoff(1)
        delay_2 = calculate_backoff(2)
        delay_3 = calculate_backoff(3)

        # Base delays: 2, 4, 8 (with jitter)
        assert 2.0 <= delay_1 <= 2.2
        assert 4.0 <= delay_2 <= 4.4
        assert 8.0 <= delay_3 <= 8.8

    def test_max_backoff(self) -> None:
        """Test maximum backoff cap."""
        delay = calculate_backoff(10)  # Would be 1024s without cap
        assert delay <= 66.0  # 60s + 10% jitter max
