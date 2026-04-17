"""GitHub OAuth authentication for the HTR service."""

from .config import AuthSettings, get_settings
from .deps import User, current_user, require_user
from .routes import router

__all__ = [
    "AuthSettings",
    "get_settings",
    "User",
    "current_user",
    "require_user",
    "router",
]
