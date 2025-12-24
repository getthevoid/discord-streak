"""Connection result and state tracking models."""

from datetime import datetime
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field


class ConnectionState(str, Enum):
    """Connection state enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class SessionState(BaseModel):
    """Tracks connection state for backoff reset."""

    connected: bool = Field(default=False)
    state: ConnectionState = Field(default=ConnectionState.DISCONNECTED)
    last_connected: datetime | None = Field(default=None)
    reconnect_attempts: int = Field(default=0)

    def mark_connected(self) -> None:
        """Mark session as successfully connected."""
        self.connected = True
        self.state = ConnectionState.CONNECTED
        self.last_connected = datetime.now()
        self.reconnect_attempts = 0

    def mark_disconnected(self) -> None:
        """Mark session as disconnected."""
        self.connected = False
        self.state = ConnectionState.DISCONNECTED

    def mark_reconnecting(self) -> None:
        """Mark session as attempting reconnection."""
        self.state = ConnectionState.RECONNECTING
        self.reconnect_attempts += 1


class ConnectionResult(BaseModel):
    """Result of a connection attempt."""

    success: bool
    error_message: str | None = None
    attempt_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    server_index: int = 0

    @classmethod
    def success_result(cls, server_index: int) -> "ConnectionResult":
        """Create a successful connection result."""
        return cls(success=True, server_index=server_index)

    @classmethod
    def failure_result(
        cls, server_index: int, error: str, attempts: int
    ) -> "ConnectionResult":
        """Create a failed connection result."""
        return cls(
            success=False,
            error_message=error,
            attempt_count=attempts,
            server_index=server_index,
        )


class User(TypedDict):
    """Discord user information."""

    id: str
    username: str
