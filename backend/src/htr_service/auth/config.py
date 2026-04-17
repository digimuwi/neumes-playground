"""Auth configuration driven entirely by environment variables.

Environment variables:
    GITHUB_CLIENT_ID        OAuth App client ID (required when AUTH_ENABLED).
    GITHUB_CLIENT_SECRET    OAuth App client secret (required when AUTH_ENABLED).
    GITHUB_ALLOWED_ORG      GitHub org whose members may sign in. Default: digimuwi.
    SESSION_SECRET          Key used to sign session cookies (required when AUTH_ENABLED).
    BACKEND_URL             Public URL of the backend (used for OAuth callback).
                            Default: http://localhost:8000.
    FRONTEND_URL            Public URL of the frontend (redirect target after login).
                            Default: http://localhost:5173.
    AUTH_ENABLED            Enable the GitHub OAuth flow. Default: false.
                            When false, endpoints are unprotected and the
                            current-user dependency returns a synthetic dev user.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AuthSettings:
    enabled: bool
    client_id: str
    client_secret: str
    allowed_org: str
    session_secret: str
    backend_url: str
    frontend_url: str

    @property
    def callback_url(self) -> str:
        return f"{self.backend_url.rstrip('/')}/auth/callback"


@lru_cache(maxsize=1)
def get_settings() -> AuthSettings:
    enabled = _get_bool("AUTH_ENABLED", False)
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
    allowed_org = os.getenv("GITHUB_ALLOWED_ORG", "digimuwi").strip()
    session_secret = os.getenv("SESSION_SECRET", "dev-insecure-session-secret")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").strip()
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").strip()

    if enabled:
        missing = [
            name for name, value in (
                ("GITHUB_CLIENT_ID", client_id),
                ("GITHUB_CLIENT_SECRET", client_secret),
            ) if not value
        ]
        if missing:
            raise RuntimeError(
                "AUTH_ENABLED is true but the following env vars are unset: "
                + ", ".join(missing)
            )
        if session_secret == "dev-insecure-session-secret":
            raise RuntimeError(
                "AUTH_ENABLED is true but SESSION_SECRET is unset. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

    return AuthSettings(
        enabled=enabled,
        client_id=client_id,
        client_secret=client_secret,
        allowed_org=allowed_org,
        session_secret=session_secret,
        backend_url=backend_url,
        frontend_url=frontend_url,
    )
