"""Git-backed storage helpers.

After a successful write, the API layer asks this module to stage + commit
the affected paths. Pushing is done asynchronously when DATA_GIT_PUSH=true.

All operations are best-effort: failures are logged and swallowed so a git
hiccup never breaks the API response.

Environment variables:
    DATA_GIT_ENABLED  Enable git commits on write. Default: false.
    DATA_GIT_PUSH     Also `git push` after each commit. Default: false.
    DATA_GIT_REMOTE   Remote name to push to. Default: origin.
    DATA_GIT_BRANCH   Branch to push. Default: the current branch.
    DATA_REPO_ROOT    Path to the git working copy. Default: repo root
                      detected from this file's location.
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class GitSettings:
    enabled: bool
    push: bool
    remote: str
    branch: str | None
    repo_root: Path


@lru_cache(maxsize=1)
def get_settings() -> GitSettings:
    repo_root_env = os.getenv("DATA_REPO_ROOT")
    repo_root = Path(repo_root_env).resolve() if repo_root_env else _DEFAULT_REPO_ROOT
    return GitSettings(
        enabled=_get_bool("DATA_GIT_ENABLED", False),
        push=_get_bool("DATA_GIT_PUSH", False),
        remote=os.getenv("DATA_GIT_REMOTE", "origin"),
        branch=os.getenv("DATA_GIT_BRANCH") or None,
        repo_root=repo_root,
    )


def _run_git(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _has_staged_changes(cwd: Path) -> bool:
    result = _run_git(["diff", "--cached", "--quiet"], cwd=cwd, check=False)
    return result.returncode == 1


def _push_async(settings: GitSettings) -> None:
    def _push() -> None:
        try:
            args = ["push", settings.remote]
            if settings.branch:
                args.append(settings.branch)
            result = _run_git(args, cwd=settings.repo_root, check=False)
            if result.returncode != 0:
                logger.warning(
                    "git push failed (rc=%d): %s", result.returncode, result.stderr.strip()
                )
            else:
                logger.info("git push ok")
        except Exception:
            logger.exception("git push threw")

    threading.Thread(target=_push, daemon=True).start()


def commit_paths(
    paths: list[Path] | list[str],
    *,
    message: str,
    author_name: str = "HTR Service",
    author_email: str = "htr-service@localhost",
) -> None:
    """Stage the given paths and create a commit. Best-effort.

    No-op when DATA_GIT_ENABLED is false or no changes were staged.
    """
    settings = get_settings()
    if not settings.enabled:
        return

    if not paths:
        return

    repo_root = settings.repo_root
    try:
        str_paths = [str(Path(p)) for p in paths]
        _run_git(["add", "--", *str_paths], cwd=repo_root)

        if not _has_staged_changes(repo_root):
            logger.debug("No staged changes for %s", str_paths)
            return

        env_overrides = {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
        }
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, **env_overrides},
        )
        if result.returncode != 0:
            logger.warning(
                "git commit failed (rc=%d): %s", result.returncode, result.stderr.strip()
            )
            return

        logger.info("git commit: %s", message)
    except Exception:
        logger.exception("git commit threw")
        return

    if settings.push:
        _push_async(settings)
