from datetime import datetime

from colorama import Fore, Style, init  # pyright: ignore[reportMissingModuleSource]

from src.types import LogLevel

init()

LEVEL_COLORS: dict[LogLevel, str] = {
    "info": Fore.CYAN,
    "warn": Fore.YELLOW,
    "error": Fore.RED,
}


def log(level: LogLevel, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = LEVEL_COLORS.get(level, Fore.WHITE)
    print(
        f"{Fore.WHITE}[{timestamp}] {color}[{level.upper()}]{Style.RESET_ALL} {message}"
    )
