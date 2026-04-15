"""Tests for the shared neume class registry."""

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from htr_service.api import app
from htr_service.models.types import NeumeClassCreate, NeumeClassUpdate
from htr_service import neume_registry


def test_load_neume_registry_from_legacy_yaml(tmp_path):
    path = tmp_path / "neume_classes.yaml"
    path.write_text("classes:\n  - punctum\n  - clivis\n", encoding="utf-8")

    classes = neume_registry.load_neume_registry(path)

    assert [entry.id for entry in classes] == [0, 1]
    assert [entry.key for entry in classes] == ["punctum", "clivis"]
    assert classes[0].name == "Punctum"
    assert classes[0].active is True


def test_create_neume_class_appends_stable_id(tmp_path):
    path = tmp_path / "neume_classes.yaml"
    path.write_text("classes:\n  - punctum\n  - clivis\n", encoding="utf-8")

    created = neume_registry.create_neume_class(
        NeumeClassCreate(key="virga strata", name="Virga Strata", description="Custom class"),
        path,
    )

    assert created.id == 2
    stored = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert stored["classes"][2]["key"] == "virga strata"
    assert stored["classes"][2]["active"] is True


def test_update_neume_class_preserves_id_and_key(tmp_path):
    path = tmp_path / "neume_classes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "classes": [
                    {"id": 0, "key": "punctum", "name": "Punctum", "description": "", "active": True},
                    {"id": 1, "key": "clivis", "name": "Clivis", "description": "", "active": True},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    updated = neume_registry.update_neume_class(
        1,
        NeumeClassUpdate(name="Clivis Revised", description="Updated", active=False),
        path,
    )

    assert updated.id == 1
    assert updated.key == "clivis"
    assert updated.active is False


def test_neume_class_api_round_trip(tmp_path, monkeypatch):
    path = tmp_path / "neume_classes.yaml"
    path.write_text("classes:\n  - punctum\n  - clivis\n", encoding="utf-8")
    monkeypatch.setattr(neume_registry, "DEFAULT_CLASSES_PATH", path)

    client = TestClient(app)

    get_response = client.get("/neume-classes")
    assert get_response.status_code == 200
    assert [entry["key"] for entry in get_response.json()] == ["punctum", "clivis"]

    create_response = client.post(
        "/neume-classes",
        json={"key": "virga strata", "name": "Virga Strata", "description": "Custom"},
    )
    assert create_response.status_code == 201
    assert create_response.json()["id"] == 2

    patch_response = client.patch(
        "/neume-classes/1",
        json={"name": "Clivis", "description": "Two-note descending", "active": False},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["active"] is False

    stored = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert stored["classes"][1]["active"] is False
