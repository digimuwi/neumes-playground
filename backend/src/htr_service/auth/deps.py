"""FastAPI dependencies for accessing the current authenticated user."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request, status

from .config import get_settings


DEV_USER_LOGIN = "local-dev"


@dataclass(frozen=True)
class User:
    login: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    @property
    def is_dev(self) -> bool:
        return self.login == DEV_USER_LOGIN


def _user_from_session(request: Request) -> Optional[User]:
    data = request.session.get("user") if hasattr(request, "session") else None
    if not data:
        return None
    login = data.get("login")
    if not login:
        return None
    return User(
        login=login,
        name=data.get("name"),
        avatar_url=data.get("avatar_url"),
    )


def current_user(request: Request) -> Optional[User]:
    """Return the authenticated user, or a synthetic dev user when auth is off."""
    settings = get_settings()
    user = _user_from_session(request)
    if user:
        return user
    if not settings.enabled:
        return User(login=DEV_USER_LOGIN)
    return None


def require_user(request: Request) -> User:
    """Require an authenticated user; raise 401 when missing."""
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
