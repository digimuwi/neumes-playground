"""Tests for training data contribution endpoint and JSON storage."""

import base64
import json
import shutil
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from htr_service.api import app
from htr_service.contribution import storage as contrib_storage
from htr_service.contribution.storage import list_contributions
from htr_service.models.types import (
    ContributionAnnotations,
    LineInput,
    NeumeInput,
    SyllableInput,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_image_bytes():
    """Create a simple valid image for testing."""
    img = Image.new("RGB", (200, 300), color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def valid_jpeg_bytes():
    """Create a simple valid JPEG image for testing."""
    img = Image.new("RGB", (200, 300), color="white")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def cleanup_contributions(tmp_path, monkeypatch):
    """Redirect contributions to a temp directory so real data is never touched."""
    test_contrib_dir = tmp_path / "contributions"
    test_contrib_dir.mkdir()
    monkeypatch.setattr(contrib_storage, "CONTRIBUTIONS_DIR", test_contrib_dir)
    yield


class TestContributeEndpoint:
    """Integration tests for /contribute endpoint."""

    def test_successful_contribution(self, client, valid_image_bytes, cleanup_contributions):
        """Test successful contribution with syllables and neumes."""
        annotations = {
            "lines": [
                {
                    "boundary": [[10, 50], [90, 50], [90, 75], [10, 75]],
                    "syllables": [
                        {"text": "Do-", "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]]},
                        {"text": "mi", "boundary": [[60, 52], [90, 52], [90, 75], [60, 75]]},
                    ]
                }
            ],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 15, "y": 30, "width": 20, "height": 18}},
            ],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["message"] == "Contribution saved successfully"

        # Verify files were created
        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / data["id"]
        assert contribution_dir.exists()
        assert (contribution_dir / "image.png").exists()
        assert (contribution_dir / "annotations.json").exists()

        # Verify annotations.json content
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert stored["image"] == {"filename": "image.png", "width": 200, "height": 300}
        assert len(stored["lines"]) == 1
        assert len(stored["lines"][0]["syllables"]) == 2
        assert len(stored["neumes"]) == 1
        assert stored["neumes"][0]["type"] == "punctum"

    def test_contribution_with_jpeg(self, client, valid_jpeg_bytes, cleanup_contributions):
        """Test contribution with JPEG image."""
        annotations = {"lines": [], "neumes": []}

        response = client.post(
            "/contribute",
            files={"image": ("test.jpg", valid_jpeg_bytes, "image/jpeg")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201
        data = response.json()

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / data["id"]
        assert (contribution_dir / "image.jpg").exists()

        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert stored["image"]["filename"] == "image.jpg"

    def test_contribution_only_syllables(self, client, valid_image_bytes, cleanup_contributions):
        """Test contribution with only syllables (no neumes)."""
        annotations = {
            "lines": [
                {
                    "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]],
                    "syllables": [
                        {"text": "Test", "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]]},
                    ]
                }
            ],
            "neumes": [],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert len(stored["lines"]) == 1
        assert stored["neumes"] == []

    def test_contribution_only_neumes(self, client, valid_image_bytes, cleanup_contributions):
        """Test contribution with only neumes stores them (not discarded)."""
        annotations = {
            "lines": [],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 10, "y": 30, "width": 20, "height": 18}},
            ],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert stored["lines"] == []
        assert len(stored["neumes"]) == 1
        assert stored["neumes"][0]["type"] == "punctum"

    def test_neumes_are_stored(self, client, valid_image_bytes, cleanup_contributions):
        """Test that neumes are persisted in annotations.json."""
        annotations = {
            "lines": [
                {
                    "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]],
                    "syllables": [
                        {"text": "Do-", "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]]},
                    ]
                }
            ],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 15, "y": 30, "width": 20, "height": 18}},
                {"type": "clivis", "bbox": {"x": 60, "y": 28, "width": 25, "height": 22}},
            ],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert len(stored["neumes"]) == 2
        assert stored["neumes"][0]["type"] == "punctum"
        assert stored["neumes"][1]["type"] == "clivis"

    def test_annotations_stored_verbatim(self, client, valid_image_bytes, cleanup_contributions):
        """Test that annotations are stored exactly as submitted (trailing hyphens preserved)."""
        annotations = {
            "lines": [
                {
                    "boundary": [[10, 50], [125, 50], [125, 75], [10, 75]],
                    "syllables": [
                        {"text": "Do-", "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]]},
                        {"text": "mi-", "boundary": [[60, 52], [90, 52], [90, 75], [60, 75]]},
                        {"text": "ne", "boundary": [[100, 51], [125, 51], [125, 75], [100, 75]]},
                    ]
                }
            ],
            "neumes": [],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        syllables = stored["lines"][0]["syllables"]
        assert syllables[0]["text"] == "Do-"
        assert syllables[1]["text"] == "mi-"
        assert syllables[2]["text"] == "ne"

    def test_any_neume_type_accepted(self, client, valid_image_bytes, cleanup_contributions):
        """Test that arbitrary neume type strings are accepted and stored."""
        annotations = {
            "lines": [],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 10, "y": 30, "width": 20, "height": 18}},
                {"type": "custom-new-type", "bbox": {"x": 40, "y": 30, "width": 20, "height": 18}},
                {"type": "virga-strata", "bbox": {"x": 70, "y": 30, "width": 20, "height": 18}},
            ],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        types = [n["type"] for n in stored["neumes"]]
        assert types == ["punctum", "custom-new-type", "virga-strata"]

    def test_missing_image(self, client):
        """Test error when image is missing."""
        annotations = {"lines": [], "neumes": []}

        response = client.post(
            "/contribute",
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 422

    def test_invalid_json(self, client, valid_image_bytes):
        """Test error when annotations JSON is invalid."""
        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": "not valid json"},
        )

        assert response.status_code == 422
        assert "Invalid JSON" in response.json()["detail"]

    def test_invalid_annotations_structure(self, client, valid_image_bytes):
        """Test error when annotations have invalid structure."""
        annotations = {
            "lines": [{"boundary": "not-a-list", "syllables": [{"text": "x", "boundary": "invalid"}]}],
            "neumes": [],
        }
        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 422

    def test_invalid_image_file(self, client):
        """Test error when image file is invalid."""
        annotations = {"lines": [], "neumes": []}

        response = client.post(
            "/contribute",
            files={"image": ("test.png", b"not an image", "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 422
        assert "Invalid image file" in response.json()["detail"]

    def test_image_metadata_in_annotations(self, client, valid_image_bytes, cleanup_contributions):
        """Test that annotations.json contains correct image metadata."""
        annotations = {"lines": [], "neumes": []}

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert stored["image"]["filename"] == "image.png"
        assert stored["image"]["width"] == 200
        assert stored["image"]["height"] == 300

    def test_empty_text_allowed(self, client, valid_image_bytes, cleanup_contributions):
        """Test that syllables with empty text are accepted."""
        annotations = {
            "lines": [
                {
                    "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]],
                    "syllables": [
                        {"text": "", "boundary": [[10, 50], [50, 50], [50, 75], [10, 75]]},
                    ]
                }
            ],
            "neumes": [],
        }

        response = client.post(
            "/contribute",
            files={"image": ("test.png", valid_image_bytes, "image/png")},
            data={"annotations": json.dumps(annotations)},
        )

        assert response.status_code == 201

        contribution_dir = contrib_storage.CONTRIBUTIONS_DIR / response.json()["id"]
        stored = json.loads((contribution_dir / "annotations.json").read_text())
        assert stored["lines"][0]["syllables"][0]["text"] == ""


class TestListContributions:
    """Tests for list_contributions()."""

    @pytest.fixture(autouse=True)
    def _setup_contributions_dir(self, tmp_path, monkeypatch):
        """Use a temporary directory for contributions."""
        self.contrib_dir = tmp_path / "contributions"
        self.contrib_dir.mkdir()
        monkeypatch.setattr(
            "htr_service.contribution.storage.CONTRIBUTIONS_DIR", self.contrib_dir
        )

    def _make_contribution(self, name, has_image=True, has_annotations=True):
        """Create a contribution directory with optional files."""
        d = self.contrib_dir / name
        d.mkdir()
        if has_image:
            img = Image.new("RGB", (100, 100), "white")
            img.save(d / "image.jpg")
        if has_annotations:
            (d / "annotations.json").write_text(
                json.dumps({"image": {"filename": "image.jpg", "width": 100, "height": 100}, "lines": [], "neumes": []})
            )

    def test_populated_directory(self):
        """List returns all valid contributions."""
        self._make_contribution("aaa")
        self._make_contribution("bbb")
        self._make_contribution("ccc")

        results = list_contributions()
        assert len(results) == 3
        ids = [r[0] for r in results]
        assert ids == ["aaa", "bbb", "ccc"]

    def test_empty_directory(self):
        """Empty contributions directory returns empty list."""
        results = list_contributions()
        assert results == []

    def test_nonexistent_directory(self, monkeypatch):
        """Nonexistent contributions directory returns empty list."""
        monkeypatch.setattr(
            "htr_service.contribution.storage.CONTRIBUTIONS_DIR",
            self.contrib_dir / "nonexistent",
        )
        results = list_contributions()
        assert results == []

    def test_skips_missing_annotations(self):
        """Skips directories missing annotations.json."""
        self._make_contribution("good")
        self._make_contribution("bad", has_annotations=False)

        results = list_contributions()
        assert len(results) == 1
        assert results[0][0] == "good"

    def test_skips_missing_image(self):
        """Skips directories missing image file."""
        self._make_contribution("good")
        self._make_contribution("bad", has_image=False)

        results = list_contributions()
        assert len(results) == 1
        assert results[0][0] == "good"

    def test_returns_paths(self):
        """Returns correct paths for each contribution."""
        self._make_contribution("abc")

        results = list_contributions()
        assert results[0][1] == self.contrib_dir / "abc"


class TestListContributionsEndpoint:
    """Tests for GET /contributions endpoint."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        self.contrib_dir = tmp_path / "contributions"
        self.contrib_dir.mkdir()
        monkeypatch.setattr(contrib_storage, "CONTRIBUTIONS_DIR", self.contrib_dir)
        self.client = TestClient(app)

    def _make_contribution(self, name, lines=None, neumes=None, has_image=True, has_annotations=True):
        d = self.contrib_dir / name
        d.mkdir()
        if has_image:
            img = Image.new("RGB", (100, 150), "white")
            img.save(d / "image.jpg")
        if has_annotations:
            (d / "annotations.json").write_text(json.dumps({
                "image": {"filename": "image.jpg", "width": 100, "height": 150},
                "lines": lines or [],
                "neumes": neumes or [],
            }))

    def test_empty_list(self):
        """Returns empty array when no contributions exist."""
        response = self.client.get("/contributions")
        assert response.status_code == 200
        assert response.json() == []

    def test_populated_list_with_counts(self):
        """Returns summaries with correct annotation counts."""
        self._make_contribution(
            "aaa",
            lines=[
                {"boundary": [[0, 0], [10, 0], [10, 10], [0, 10]], "syllables": [
                    {"text": "Do-", "boundary": [[0, 0], [5, 0], [5, 10], [0, 10]]},
                    {"text": "mi", "boundary": [[5, 0], [10, 0], [10, 10], [5, 10]]},
                ]},
                {"boundary": [[0, 20], [10, 20], [10, 30], [0, 30]], "syllables": [
                    {"text": "ne", "boundary": [[0, 20], [10, 20], [10, 30], [0, 30]]},
                ]},
            ],
            neumes=[
                {"type": "punctum", "bbox": {"x": 1, "y": 1, "width": 5, "height": 5}},
                {"type": "clivis", "bbox": {"x": 10, "y": 1, "width": 5, "height": 5}},
            ],
        )
        self._make_contribution("bbb")

        response = self.client.get("/contributions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        aaa = next(s for s in data if s["id"] == "aaa")
        assert aaa["line_count"] == 2
        assert aaa["syllable_count"] == 3
        assert aaa["neume_count"] == 2
        assert aaa["image"]["width"] == 100
        assert aaa["image"]["height"] == 150

        bbb = next(s for s in data if s["id"] == "bbb")
        assert bbb["line_count"] == 0
        assert bbb["syllable_count"] == 0
        assert bbb["neume_count"] == 0

    def test_skips_malformed(self):
        """Malformed contributions are excluded from list."""
        self._make_contribution("good")
        self._make_contribution("bad", has_image=False)

        response = self.client.get("/contributions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "good"


class TestGetContributionEndpoint:
    """Tests for GET /contributions/{id} endpoint."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        self.contrib_dir = tmp_path / "contributions"
        self.contrib_dir.mkdir()
        monkeypatch.setattr(contrib_storage, "CONTRIBUTIONS_DIR", self.contrib_dir)
        self.client = TestClient(app)

    def _make_contribution(self, name):
        d = self.contrib_dir / name
        d.mkdir()
        img = Image.new("RGB", (100, 150), "white")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        (d / "image.jpg").write_bytes(buf.getvalue())
        (d / "annotations.json").write_text(json.dumps({
            "image": {"filename": "image.jpg", "width": 100, "height": 150},
            "lines": [
                {"boundary": [[0, 0], [10, 0], [10, 10], [0, 10]], "syllables": [
                    {"text": "Te", "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]]},
                ]},
            ],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 1, "y": 1, "width": 5, "height": 5}},
            ],
        }))

    def test_successful_retrieval(self):
        """Returns full contribution data with base64 image."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440000"
        self._make_contribution(contrib_id)

        response = self.client.get(f"/contributions/{contrib_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == contrib_id
        assert data["image"]["filename"] == "image.jpg"
        assert data["image"]["width"] == 100
        assert data["image"]["height"] == 150
        assert data["image"]["data_url"].startswith("data:image/jpeg;base64,")

        # Verify the base64 decodes to valid image bytes
        b64_part = data["image"]["data_url"].split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        img = Image.open(BytesIO(decoded))
        assert img.size == (100, 150)

        assert len(data["lines"]) == 1
        assert data["lines"][0]["syllables"][0]["text"] == "Te"
        assert len(data["neumes"]) == 1
        assert data["neumes"][0]["type"] == "punctum"

    def test_not_found(self):
        """Returns 404 for non-existent contribution."""
        response = self.client.get("/contributions/550e8400-e29b-41d4-a716-446655440099")
        assert response.status_code == 404

    def test_invalid_uuid(self):
        """Returns 404 for non-UUID string (path traversal protection)."""
        response = self.client.get("/contributions/../../etc/passwd")
        assert response.status_code == 404

    def test_invalid_uuid_simple(self):
        """Returns 404 for non-UUID string."""
        response = self.client.get("/contributions/not-a-uuid")
        assert response.status_code == 404


class TestUpdateContributionEndpoint:
    """Tests for PUT /contributions/{id} endpoint."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        self.contrib_dir = tmp_path / "contributions"
        self.contrib_dir.mkdir()
        monkeypatch.setattr(contrib_storage, "CONTRIBUTIONS_DIR", self.contrib_dir)
        self.client = TestClient(app)

    def _make_contribution(self, name):
        d = self.contrib_dir / name
        d.mkdir()
        img = Image.new("RGB", (200, 300), "white")
        img.save(d / "image.png")
        (d / "annotations.json").write_text(json.dumps({
            "image": {"filename": "image.png", "width": 200, "height": 300},
            "lines": [
                {"boundary": [[0, 0], [10, 0], [10, 10], [0, 10]], "syllables": [
                    {"text": "Old", "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]]},
                ]},
            ],
            "neumes": [],
        }))

    def test_successful_update(self):
        """Updates annotations and preserves image metadata."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440001"
        self._make_contribution(contrib_id)

        new_annotations = {
            "lines": [
                {"boundary": [[0, 0], [20, 0], [20, 10], [0, 10]], "syllables": [
                    {"text": "New-", "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]]},
                    {"text": "text", "boundary": [[10, 0], [20, 0], [20, 10], [10, 10]]},
                ]},
            ],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 5, "y": 5, "width": 10, "height": 8}},
            ],
        }

        response = self.client.put(
            f"/contributions/{contrib_id}",
            json=new_annotations,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == contrib_id
        assert data["message"] == "Contribution updated successfully"

        # Verify stored file
        stored = json.loads(
            (self.contrib_dir / contrib_id / "annotations.json").read_text()
        )
        # Image metadata preserved
        assert stored["image"] == {"filename": "image.png", "width": 200, "height": 300}
        # Annotations replaced
        assert len(stored["lines"]) == 1
        assert len(stored["lines"][0]["syllables"]) == 2
        assert stored["lines"][0]["syllables"][0]["text"] == "New-"
        assert len(stored["neumes"]) == 1
        assert stored["neumes"][0]["type"] == "punctum"

    def test_not_found(self):
        """Returns 404 for non-existent contribution."""
        response = self.client.put(
            "/contributions/550e8400-e29b-41d4-a716-446655440099",
            json={"lines": [], "neumes": []},
        )
        assert response.status_code == 404

    def test_invalid_annotations(self):
        """Returns 422 for invalid annotations body."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440001"
        self._make_contribution(contrib_id)

        response = self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [{"boundary": "not-a-list"}], "neumes": []},
        )
        assert response.status_code == 422

    def test_invalid_uuid(self):
        """Returns 404 for non-UUID string."""
        response = self.client.put(
            "/contributions/not-a-uuid",
            json={"lines": [], "neumes": []},
        )
        assert response.status_code == 404

    def test_get_returns_version_and_etag(self):
        """GET /contributions/{id} includes version in body and ETag header."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440030"
        self._make_contribution(contrib_id)

        response = self.client.get(f"/contributions/{contrib_id}")
        assert response.status_code == 200
        version = response.json()["version"]
        assert isinstance(version, str) and len(version) == 64
        assert response.headers["etag"].strip('"') == version

    def test_update_with_matching_if_match_succeeds(self):
        """PUT with correct If-Match header succeeds and returns a new version."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440031"
        self._make_contribution(contrib_id)
        version = self.client.get(f"/contributions/{contrib_id}").json()["version"]

        response = self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [], "neumes": []},
            headers={"If-Match": f'"{version}"'},
        )
        assert response.status_code == 200
        new_version = response.json()["version"]
        assert new_version and new_version != version
        assert response.headers["etag"].strip('"') == new_version

    def test_update_with_stale_if_match_returns_412(self):
        """PUT with stale If-Match returns 412 and does not overwrite."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440032"
        self._make_contribution(contrib_id)
        stale_version = self.client.get(f"/contributions/{contrib_id}").json()["version"]

        # Simulate another writer updating the file
        self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [], "neumes": [
                {"type": "punctum", "bbox": {"x": 1, "y": 1, "width": 2, "height": 2}},
            ]},
        )

        response = self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [], "neumes": []},
            headers={"If-Match": f'"{stale_version}"'},
        )
        assert response.status_code == 412
        assert "modified by someone else" in response.json()["detail"]
        # Ensure the intervening write was NOT reverted
        stored = json.loads(
            (self.contrib_dir / contrib_id / "annotations.json").read_text()
        )
        assert len(stored["neumes"]) == 1

    def test_update_without_if_match_still_works(self):
        """PUT without If-Match succeeds (backwards-compatible, logs warning)."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440033"
        self._make_contribution(contrib_id)

        response = self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [], "neumes": []},
        )
        assert response.status_code == 200
        assert response.json()["version"]

    def test_update_with_wildcard_if_match_skips_check(self):
        """PUT with If-Match: * bypasses the version check per RFC 7232."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440034"
        self._make_contribution(contrib_id)

        response = self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [], "neumes": []},
            headers={"If-Match": "*"},
        )
        assert response.status_code == 200

    def test_relabel_with_stale_if_match_returns_412(self):
        """PATCH /neumes with stale If-Match returns 412."""
        contrib_id = "550e8400-e29b-41d4-a716-446655440035"
        d = self.contrib_dir / contrib_id
        d.mkdir()
        Image.new("RGB", (200, 300), "white").save(d / "image.png")
        (d / "annotations.json").write_text(json.dumps({
            "image": {"filename": "image.png", "width": 200, "height": 300},
            "lines": [],
            "neumes": [
                {"type": "punctum", "bbox": {"x": 1, "y": 2, "width": 3, "height": 4}},
            ],
        }))
        stale_version = self.client.get(f"/contributions/{contrib_id}").json()["version"]

        # Bump the file via an unchecked PUT
        self.client.put(
            f"/contributions/{contrib_id}",
            json={"lines": [], "neumes": [
                {"type": "virga", "bbox": {"x": 1, "y": 2, "width": 3, "height": 4}},
            ]},
        )

        response = self.client.patch(
            f"/contributions/{contrib_id}/neumes",
            json={"bbox": {"x": 1, "y": 2, "width": 3, "height": 4}, "new_type": "clivis"},
            headers={"If-Match": f'"{stale_version}"'},
        )
        assert response.status_code == 412
