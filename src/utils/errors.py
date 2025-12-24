"""Custom exceptions for discord-streak."""


class DiscordStreakError(Exception):
    """Base exception for discord-streak errors."""


class ConfigError(DiscordStreakError):
    """Raised when configuration is invalid."""


class AuthenticationError(DiscordStreakError):
    """Raised when Discord token is invalid or authentication fails."""


class ConnectionError(DiscordStreakError):
    """Raised when Discord connection fails."""
