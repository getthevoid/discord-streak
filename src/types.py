from typing import Literal, TypedDict

Status = Literal["online", "idle", "dnd"]
LogLevel = Literal["info", "warn", "error"]


class User(TypedDict):
    id: str
    username: str
