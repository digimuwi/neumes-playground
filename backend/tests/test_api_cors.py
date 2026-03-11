"""Tests for API CORS configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from htr_service.cors import build_cors_options


class TestCorsConfiguration:
    """Tests for backend CORS behavior."""

    def test_default_options_allow_ipv4_frontend_origins(self):
        """IP-based frontend origins are allowed by default."""
        options = build_cors_options()

        assert "http://localhost:5173" in options["allow_origins"]
        assert options["allow_origin_regex"] == r"^https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?$"

    def test_env_can_extend_origins_and_override_regex(self, monkeypatch):
        """Operators can provide extra origins and a custom regex via env."""
        monkeypatch.setenv(
            "HTR_CORS_ALLOW_ORIGINS",
            "https://frontend.example,http://134.2.227.44:4173",
        )
        monkeypatch.setenv("HTR_CORS_ALLOW_ORIGIN_REGEX", r"^https://.*\.example$")

        options = build_cors_options()

        assert "https://frontend.example" in options["allow_origins"]
        assert "http://134.2.227.44:4173" in options["allow_origins"]
        assert options["allow_origin_regex"] == r"^https://.*\.example$"

    def test_preflight_allows_ip_origin(self):
        """The live middleware accepts requests from IP-based frontend origins."""
        app = FastAPI()
        app.add_middleware(CORSMiddleware, **build_cors_options())

        @app.get("/training/status")
        async def training_status():
            return {"state": "idle"}

        client = TestClient(app)

        response = client.options(
            "/training/status",
            headers={
                "Origin": "http://134.2.227.44:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://134.2.227.44:5173"
