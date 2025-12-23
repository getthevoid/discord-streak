from dataclasses import dataclass, field
from typing import Literal, NamedTuple, TypedDict

Status = Literal["online", "idle", "dnd"]
LogLevel = Literal["info", "warn", "error"]


@dataclass
class SessionState:
    """Tracks connection state for backoff reset."""

    connected: bool = field(default=False)


class User(TypedDict):
    id: str
    username: str


class Server(NamedTuple):
    guild_id: str
    channel_id: str
