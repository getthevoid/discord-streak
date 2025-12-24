"""Colored logging utility."""

from datetime import datetime
from typing import Literal

from colorama import Fore, Style, init

init()

LogLevel = Literal["info", "warn", "error"]

LEVEL_COLORS: dict[LogLevel, str] = {
    "info": Fore.CYAN,
    "warn": Fore.YELLOW,
    "error": Fore.RED,
}


def log(level: LogLevel, message: str) -> None:
    """Log a message with colored level indicator."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = LEVEL_COLORS.get(level, Fore.WHITE)
    print(
        f"{Fore.WHITE}[{timestamp}] {color}[{level.upper()}]{Style.RESET_ALL} {message}"
    )
