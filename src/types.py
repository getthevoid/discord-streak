from dataclasses import dataclass, field
from typing import Literal, NamedTuple, TypedDict

Status = Literal["online", "idle", "dnd"]
LogLevel = Literal["info", "warn", "error"]


@dataclass
class SessionState:
    """Tracks Discord Gateway session state for resumption."""

    session_id: str | None = None
    sequence: int | None = None
    resume_gateway_url: str | None = None
    last_heartbeat_acked: bool = field(default=True)
    connected: bool = field(default=False)

    def can_resume(self) -> bool:
        """Check if we have enough state to attempt a resume."""
        return self.session_id is not None and self.sequence is not None

    def reset(self) -> None:
        """Reset session state after invalid session."""
        self.session_id = None
        self.sequence = None
        self.resume_gateway_url = None
        self.last_heartbeat_acked = True
        self.connected = False


class User(TypedDict):
    id: str
    username: str


class Server(NamedTuple):
    guild_id: str
    channel_id: str
