"""Thin GitHub OAuth + REST client used by the auth flow."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class GitHubUser:
    login: str
    name: str | None
    avatar_url: str | None


class OAuthError(Exception):
    """Raised when the GitHub OAuth exchange fails."""


async def exchange_code_for_token(
    *, client_id: str, client_secret: str, code: str, redirect_uri: str,
) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )

    if resp.status_code != 200:
        raise OAuthError(f"Token endpoint returned {resp.status_code}: {resp.text}")

    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise OAuthError(f"GitHub did not return an access token: {payload}")
    return token


async def fetch_user(token: str) -> GitHubUser:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GITHUB_API}/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )

    if resp.status_code != 200:
        raise OAuthError(f"GitHub /user returned {resp.status_code}: {resp.text}")

    data = resp.json()
    login = data.get("login")
    if not login:
        raise OAuthError("GitHub /user response missing 'login'")
    return GitHubUser(login=login, name=data.get("name"), avatar_url=data.get("avatar_url"))


async def check_org_membership(token: str, org: str, username: str) -> bool:
    """Return True if the authenticated user is a member of the given org.

    Uses GET /user/memberships/orgs/{org}, which works for private memberships
    provided the token has the read:org scope.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GITHUB_API}/user/memberships/orgs/{org}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )

    if resp.status_code == 200:
        data = resp.json()
        state = data.get("state")
        return state == "active"
    if resp.status_code in (403, 404):
        return False
    raise OAuthError(f"GitHub org membership check returned {resp.status_code}: {resp.text}")
