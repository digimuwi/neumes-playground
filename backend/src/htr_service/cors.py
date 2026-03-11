"""CORS configuration for the HTR API."""

import os


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]
DEFAULT_CORS_ORIGIN_REGEX = r"^https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?$"


def parse_cors_origins(value: str | None) -> list[str]:
    """Parse a comma/newline-separated origin list from env."""
    if not value:
        return []

    origins: list[str] = []
    for raw_origin in value.replace("\n", ",").split(","):
        origin = raw_origin.strip()
        if origin and origin not in origins:
            origins.append(origin)
    return origins


def build_cors_options() -> dict:
    """Build CORS config from defaults plus optional environment overrides."""
    allow_origins = DEFAULT_CORS_ORIGINS.copy()
    for origin in parse_cors_origins(os.getenv("HTR_CORS_ALLOW_ORIGINS")):
        if origin not in allow_origins:
            allow_origins.append(origin)

    allow_origin_regex = os.getenv("HTR_CORS_ALLOW_ORIGIN_REGEX") or DEFAULT_CORS_ORIGIN_REGEX

    return {
        "allow_origins": allow_origins,
        "allow_origin_regex": allow_origin_regex,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
