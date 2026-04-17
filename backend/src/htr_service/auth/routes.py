"""HTTP routes for the GitHub OAuth flow."""

from __future__ import annotations

import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from .config import get_settings
from .deps import current_user
from .github import (
    GITHUB_AUTHORIZE_URL,
    OAuthError,
    check_org_membership,
    exchange_code_for_token,
    fetch_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request, redirect: str | None = Query(None)):
    """Kick off the GitHub OAuth flow.

    When auth is disabled this endpoint is a no-op redirect back to the
    frontend so local dev can keep working with the same entry point.
    """
    settings = get_settings()
    target = redirect or settings.frontend_url

    if not settings.enabled:
        return RedirectResponse(target)

    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state
    request.session["post_login_redirect"] = target

    params = {
        "client_id": settings.client_id,
        "redirect_uri": settings.callback_url,
        "scope": "read:org",
        "state": state,
        "allow_signup": "false",
    }
    return RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}")


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
):
    settings = get_settings()

    if not settings.enabled:
        return RedirectResponse(settings.frontend_url)

    if error:
        raise HTTPException(status_code=400, detail=f"GitHub returned error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    expected_state = request.session.pop("oauth_state", None)
    post_login = request.session.pop("post_login_redirect", settings.frontend_url)
    if not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    try:
        token = await exchange_code_for_token(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            code=code,
            redirect_uri=settings.callback_url,
        )
        gh_user = await fetch_user(token)
        is_member = await check_org_membership(token, settings.allowed_org, gh_user.login)
    except OAuthError as exc:
        logger.exception("GitHub OAuth exchange failed")
        raise HTTPException(status_code=502, detail=str(exc))

    if not is_member:
        logger.info("Denying login for %s: not a member of %s", gh_user.login, settings.allowed_org)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User {gh_user.login} is not a member of the {settings.allowed_org} organization",
        )

    request.session["user"] = {
        "login": gh_user.login,
        "name": gh_user.name,
        "avatar_url": gh_user.avatar_url,
    }
    logger.info("Authenticated %s", gh_user.login)
    return RedirectResponse(post_login)


@router.get("/me")
async def me(request: Request):
    user = current_user(request)
    if user is None:
        return JSONResponse({"authenticated": False, "auth_enabled": get_settings().enabled})
    return {
        "authenticated": True,
        "auth_enabled": get_settings().enabled,
        "user": {
            "login": user.login,
            "name": user.name,
            "avatar_url": user.avatar_url,
        },
    }


@router.post("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return {"ok": True}
