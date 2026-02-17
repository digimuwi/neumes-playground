"""Tests for YOLO training orchestration module."""

import logging
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from htr_service.models.types import TrainingStatus
from htr_service.training import yolo_trainer
from htr_service.training.yolo_trainer import (
    TrainingAlreadyRunningError,
    _training_loop,
    get_training_status,
    start_training,
)


@pytest.fixture(autouse=True)
def reset_training_state(monkeypatch):
    """Reset the module-level training status before each test."""
    monkeypatch.setattr(yolo_trainer, "_training_status", TrainingStatus())
    # Replace the lock to avoid interference between tests
    monkeypatch.setattr(yolo_trainer, "_training_lock", threading.Lock())


class TestGetTrainingStatus:
    """Tests for get_training_status."""

    def test_returns_idle_initially(self):
        """Returns idle state when no training has been started."""
        status = get_training_status()
        assert status.state == "idle"

    def test_returns_copy(self):
        """Returns a copy, not a reference to the internal status."""
        status1 = get_training_status()
        status2 = get_training_status()
        assert status1 is not status2


class TestStartTraining:
    """Tests for start_training."""

    def test_rejects_concurrent_runs(self, monkeypatch):
        """Raises TrainingAlreadyRunningError when training is already in progress."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="training"),
        )
        with pytest.raises(TrainingAlreadyRunningError, match="already in progress"):
            start_training()

    def test_rejects_during_exporting(self, monkeypatch):
        """Rejects when in exporting state."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="exporting"),
        )
        with pytest.raises(TrainingAlreadyRunningError):
            start_training()

    def test_rejects_during_deploying(self, monkeypatch):
        """Rejects when in deploying state."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="deploying"),
        )
        with pytest.raises(TrainingAlreadyRunningError):
            start_training()

    def test_sets_exporting_state(self, monkeypatch):
        """Sets state to 'exporting' and starts_at on successful start."""
        # Mock the thread so training doesn't actually run
        mock_thread = MagicMock()
        monkeypatch.setattr(yolo_trainer.threading, "Thread", MagicMock(return_value=mock_thread))

        status = start_training(epochs=50, imgsz=320)
        assert status.state == "exporting"
        assert status.total_epochs == 50
        assert status.started_at is not None
        mock_thread.start.assert_called_once()

    def test_allows_restart_after_complete(self, monkeypatch):
        """Can start training after a previous run completed."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="complete"),
        )
        mock_thread = MagicMock()
        monkeypatch.setattr(yolo_trainer.threading, "Thread", MagicMock(return_value=mock_thread))

        status = start_training()
        assert status.state == "exporting"

    def test_allows_restart_after_failure(self, monkeypatch):
        """Can start training after a previous run failed."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="failed", error="some error"),
        )
        mock_thread = MagicMock()
        monkeypatch.setattr(yolo_trainer.threading, "Thread", MagicMock(return_value=mock_thread))

        status = start_training()
        assert status.state == "exporting"


class TestTrainingLoop:
    """Tests for _training_loop."""

    def test_state_transitions(self, tmp_path, monkeypatch):
        """Training loop transitions through exporting → training → deploying → complete."""
        # Set initial state as start_training would
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="exporting", total_epochs=5, started_at="2026-01-01T00:00:00Z"),
        )
        monkeypatch.setattr(yolo_trainer, "MODELS_DIR", tmp_path / "models")
        monkeypatch.setattr(yolo_trainer, "YOLO_MODEL_PATH", tmp_path / "models" / "neume_detector.pt")
        monkeypatch.setattr(yolo_trainer, "VERSIONS_DIR", tmp_path / "models" / "neume_versions")

        # Mock export to succeed
        dataset_dir = tmp_path / "dataset"
        dataset_yaml = dataset_dir / "dataset.yaml"
        dataset_yaml.parent.mkdir(parents=True)
        dataset_yaml.write_text("path: .\ntrain: images/train\nval: images/val\nnames:\n  0: punctum\n")
        monkeypatch.setattr(yolo_trainer, "DEFAULT_OUTPUT_DIR", dataset_dir)

        mock_export = MagicMock(return_value={"exported": 3, "skipped": 0, "train": 2, "val": 1})
        monkeypatch.setattr("htr_service.training.yolo_trainer.export_dataset", mock_export)

        # Mock YOLO model training
        mock_results = MagicMock()
        weights_dir = tmp_path / "runs" / "weights"
        weights_dir.mkdir(parents=True)
        best_weights = weights_dir / "best.pt"
        best_weights.write_bytes(b"fake model weights")
        mock_results.save_dir = str(weights_dir.parent)

        mock_model = MagicMock()
        mock_model.train.return_value = mock_results

        mock_yolo_cls = MagicMock(return_value=mock_model)
        with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=mock_yolo_cls)}):
            _training_loop(epochs=5, imgsz=640)

        status = yolo_trainer._training_status
        assert status.state == "complete"
        assert status.current_epoch == 5
        assert status.total_epochs == 5
        assert status.model_version is not None
        assert status.completed_at is not None

    def test_model_versioning(self, tmp_path, monkeypatch):
        """Trained model is saved to neume_versions/ with timestamp."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="exporting", total_epochs=5, started_at="2026-01-01T00:00:00Z"),
        )
        versions_dir = tmp_path / "models" / "neume_versions"
        monkeypatch.setattr(yolo_trainer, "MODELS_DIR", tmp_path / "models")
        monkeypatch.setattr(yolo_trainer, "YOLO_MODEL_PATH", tmp_path / "models" / "neume_detector.pt")
        monkeypatch.setattr(yolo_trainer, "VERSIONS_DIR", versions_dir)

        dataset_dir = tmp_path / "dataset"
        dataset_yaml = dataset_dir / "dataset.yaml"
        dataset_yaml.parent.mkdir(parents=True)
        dataset_yaml.write_text("dummy")
        monkeypatch.setattr(yolo_trainer, "DEFAULT_OUTPUT_DIR", dataset_dir)

        mock_export = MagicMock(return_value={"exported": 1, "skipped": 0, "train": 1, "val": 0})
        monkeypatch.setattr("htr_service.training.yolo_trainer.export_dataset", mock_export)

        weights_dir = tmp_path / "runs" / "weights"
        weights_dir.mkdir(parents=True)
        (weights_dir / "best.pt").write_bytes(b"model data")

        mock_results = MagicMock()
        mock_results.save_dir = str(weights_dir.parent)
        mock_model = MagicMock()
        mock_model.train.return_value = mock_results
        mock_yolo_cls = MagicMock(return_value=mock_model)

        with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=mock_yolo_cls)}):
            _training_loop(epochs=5, imgsz=640)

        # Version directory should exist with a .pt file
        assert versions_dir.exists()
        pt_files = list(versions_dir.glob("*.pt"))
        assert len(pt_files) == 1
        assert pt_files[0].stat().st_size > 0

    def test_atomic_deployment(self, tmp_path, monkeypatch):
        """Model is atomically deployed to neume_detector.pt."""
        model_path = tmp_path / "models" / "neume_detector.pt"
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="exporting", total_epochs=5, started_at="2026-01-01T00:00:00Z"),
        )
        monkeypatch.setattr(yolo_trainer, "MODELS_DIR", tmp_path / "models")
        monkeypatch.setattr(yolo_trainer, "YOLO_MODEL_PATH", model_path)
        monkeypatch.setattr(yolo_trainer, "VERSIONS_DIR", tmp_path / "models" / "neume_versions")

        dataset_dir = tmp_path / "dataset"
        dataset_yaml = dataset_dir / "dataset.yaml"
        dataset_yaml.parent.mkdir(parents=True)
        dataset_yaml.write_text("dummy")
        monkeypatch.setattr(yolo_trainer, "DEFAULT_OUTPUT_DIR", dataset_dir)

        mock_export = MagicMock(return_value={"exported": 1, "skipped": 0, "train": 1, "val": 0})
        monkeypatch.setattr("htr_service.training.yolo_trainer.export_dataset", mock_export)

        weights_dir = tmp_path / "runs" / "weights"
        weights_dir.mkdir(parents=True)
        (weights_dir / "best.pt").write_bytes(b"deployed model")

        mock_results = MagicMock()
        mock_results.save_dir = str(weights_dir.parent)
        mock_model = MagicMock()
        mock_model.train.return_value = mock_results
        mock_yolo_cls = MagicMock(return_value=mock_model)

        with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=mock_yolo_cls)}):
            _training_loop(epochs=5, imgsz=640)

        assert model_path.exists()
        assert model_path.read_bytes() == b"deployed model"
        # No temp files left behind
        tmp_files = list((tmp_path / "models").glob(".neume_detector_*.tmp"))
        assert tmp_files == []

    def test_exception_sets_failed_state(self, monkeypatch):
        """Training loop catches exceptions and sets state to 'failed'."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="exporting", total_epochs=5, started_at="2026-01-01T00:00:00Z"),
        )

        mock_export = MagicMock(side_effect=RuntimeError("disk full"))
        monkeypatch.setattr("htr_service.training.yolo_trainer.export_dataset", mock_export)

        _training_loop(epochs=5, imgsz=640)

        status = yolo_trainer._training_status
        assert status.state == "failed"
        assert "disk full" in status.error

    def test_no_contributions_sets_failed(self, monkeypatch):
        """Sets failed state when export produces 0 images."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(state="exporting", total_epochs=5, started_at="2026-01-01T00:00:00Z"),
        )

        mock_export = MagicMock(return_value={"exported": 0, "skipped": 3, "train": 0, "val": 0})
        monkeypatch.setattr("htr_service.training.yolo_trainer.export_dataset", mock_export)

        _training_loop(epochs=5, imgsz=640)

        status = yolo_trainer._training_status
        assert status.state == "failed"
        assert "No training data" in status.error


class TestTrainingEndpoints:
    """Tests for the API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from htr_service.api import app
        return TestClient(app)

    def test_get_status_idle(self, client, monkeypatch):
        """GET /training/status returns idle initially."""
        monkeypatch.setattr(yolo_trainer, "_training_status", TrainingStatus())
        # Also patch the imported reference in api module
        monkeypatch.setattr("htr_service.api.get_training_status", get_training_status)

        resp = client.get("/training/status")
        assert resp.status_code == 200
        assert resp.json()["state"] == "idle"

    def test_get_status_during_training(self, client, monkeypatch):
        """GET /training/status reflects training progress."""
        monkeypatch.setattr(
            yolo_trainer, "_training_status",
            TrainingStatus(
                state="training", current_epoch=42, total_epochs=100,
                started_at="2026-01-01T00:00:00Z",
            ),
        )
        monkeypatch.setattr("htr_service.api.get_training_status", get_training_status)

        resp = client.get("/training/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "training"
        assert data["current_epoch"] == 42
        assert data["total_epochs"] == 100

    def test_post_start_returns_202(self, client, monkeypatch):
        """POST /training/start returns 202 and starts training."""
        mock_status = TrainingStatus(state="exporting", started_at="2026-01-01T00:00:00Z")
        mock_start = MagicMock(return_value=mock_status)
        monkeypatch.setattr("htr_service.api.start_training", mock_start)

        resp = client.post("/training/start", json={"epochs": 50, "imgsz": 320})
        assert resp.status_code == 202
        assert resp.json()["state"] == "exporting"
        mock_start.assert_called_once_with(epochs=50, imgsz=320)

    def test_post_start_default_params(self, client, monkeypatch):
        """POST /training/start with no body uses defaults."""
        mock_status = TrainingStatus(state="exporting", started_at="2026-01-01T00:00:00Z")
        mock_start = MagicMock(return_value=mock_status)
        monkeypatch.setattr("htr_service.api.start_training", mock_start)

        resp = client.post("/training/start")
        assert resp.status_code == 202
        mock_start.assert_called_once_with(epochs=100, imgsz=640)

    def test_post_start_409_when_running(self, client, monkeypatch):
        """POST /training/start returns 409 when training is in progress."""
        mock_start = MagicMock(side_effect=TrainingAlreadyRunningError("Training already in progress"))
        monkeypatch.setattr("htr_service.api.start_training", mock_start)

        resp = client.post("/training/start")
        assert resp.status_code == 409
        assert "already in progress" in resp.json()["detail"]


class TestNeumeDetectionWarning:
    """Tests for updated warning message in neume detection."""

    def test_warning_references_training_endpoint(self, tmp_path, monkeypatch, caplog):
        """Warning message mentions POST /training/start."""
        from htr_service.pipeline import neume_detection as nd

        monkeypatch.setattr(nd, "YOLO_MODEL_PATH", tmp_path / "nonexistent.pt")
        monkeypatch.setattr(nd, "_yolo_cache", None)

        with caplog.at_level(logging.WARNING, logger="htr_service.pipeline.neume_detection"):
            from htr_service.pipeline.neume_detection import detect_neumes
            detect_neumes(
                Image.new("RGB", (100, 100), color=(180, 160, 140)),
                MagicMock(lines=[]),
            )

        assert any("/training/start" in msg for msg in caplog.messages)
