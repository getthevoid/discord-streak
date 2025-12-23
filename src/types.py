from typing import Literal, NamedTuple, TypedDict

Status = Literal["online", "idle", "dnd"]
LogLevel = Literal["info", "warn", "error"]


class User(TypedDict):
    id: str
    username: str


class Server(NamedTuple):
    guild_id: str
    channel_id: str
