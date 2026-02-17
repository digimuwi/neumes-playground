"""Tests for YOLO training data export pipeline."""

import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml
from PIL import Image

from htr_service.training.yolo_export import (
    bbox_to_yolo,
    load_neume_classes,
    export_dataset,
    _assign_bboxes_to_tile,
)


# --- 5.1 YOLO bbox normalization ---


class TestBboxToYolo:
    """Test YOLO normalized bbox conversion."""

    def test_basic_conversion(self):
        """Pixel bbox converts to normalized center format."""
        xc, yc, w, h = bbox_to_yolo(
            x=100, y=200, width=40, height=30,
            img_w=1000, img_h=1000,
        )
        assert xc == pytest.approx(0.12)   # (100 + 20) / 1000
        assert yc == pytest.approx(0.215)  # (200 + 15) / 1000
        assert w == pytest.approx(0.04)    # 40 / 1000
        assert h == pytest.approx(0.03)    # 30 / 1000

    def test_full_image_bbox(self):
        """Bbox covering the entire image normalizes to center (0.5, 0.5) with size (1, 1)."""
        xc, yc, w, h = bbox_to_yolo(
            x=0, y=0, width=800, height=600,
            img_w=800, img_h=600,
        )
        assert xc == pytest.approx(0.5)
        assert yc == pytest.approx(0.5)
        assert w == pytest.approx(1.0)
        assert h == pytest.approx(1.0)

    def test_asymmetric_image(self):
        """Normalization uses correct axis for each dimension."""
        xc, yc, w, h = bbox_to_yolo(
            x=50, y=100, width=20, height=10,
            img_w=200, img_h=400,
        )
        assert xc == pytest.approx(0.3)    # (50 + 10) / 200
        assert yc == pytest.approx(0.2625) # (100 + 5) / 400
        assert w == pytest.approx(0.1)     # 20 / 200
        assert h == pytest.approx(0.025)   # 10 / 400


# --- 5.2 Class mapping ---


class TestLoadNeumeClasses:
    """Test neume class YAML loading."""

    def test_loads_correct_mapping(self, tmp_path):
        """YAML class list maps to 0-indexed IDs."""
        yaml_path = tmp_path / "classes.yaml"
        yaml_path.write_text("classes:\n  - punctum\n  - clivis\n  - podatus\n")

        result = load_neume_classes(yaml_path)
        assert result == {"punctum": 0, "clivis": 1, "podatus": 2}

    def test_missing_file_raises(self, tmp_path):
        """Missing YAML file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_neume_classes(tmp_path / "nonexistent.yaml")

    def test_invalid_structure_raises(self, tmp_path):
        """YAML without 'classes' key raises ValueError."""
        yaml_path = tmp_path / "bad.yaml"
        yaml_path.write_text("something_else:\n  - a\n")

        with pytest.raises(ValueError, match="classes"):
            load_neume_classes(yaml_path)


# --- Fixtures for export tests ---


@pytest.fixture
def export_env(tmp_path):
    """Set up a complete export environment with contributions and classes."""
    contrib_dir = tmp_path / "contributions"
    contrib_dir.mkdir()
    output_dir = tmp_path / "dataset"
    classes_path = tmp_path / "neume_classes.yaml"
    classes_path.write_text("classes:\n  - punctum\n  - clivis\n  - podatus\n")

    def make_contribution(name, neumes, img_size=(200, 300), lines=None):
        d = contrib_dir / name
        d.mkdir()
        img = Image.new("RGB", img_size, "beige")
        img.save(d / "image.jpg")
        annotations = {
            "image": {"filename": "image.jpg", "width": img_size[0], "height": img_size[1]},
            "lines": lines if lines is not None else [],
            "neumes": neumes,
        }
        (d / "annotations.json").write_text(json.dumps(annotations))

    return {
        "contrib_dir": contrib_dir,
        "output_dir": output_dir,
        "classes_path": classes_path,
        "make_contribution": make_contribution,
    }


def _run_export(env, **kwargs):
    """Run export with mocked contribution dir."""
    with patch(
        "htr_service.training.yolo_export.list_contributions",
    ) as mock_list, patch(
        "htr_service.contribution.storage.CONTRIBUTIONS_DIR",
        env["contrib_dir"],
    ):
        # Build contributions list from actual directory
        entries = []
        for d in sorted(env["contrib_dir"].iterdir()):
            if d.is_dir() and (d / "annotations.json").is_file():
                entries.append((d.name, d))
        mock_list.return_value = entries

        return export_dataset(
            output_dir=env["output_dir"],
            classes_path=env["classes_path"],
            **kwargs,
        )


# --- 5.3 Export with mock contributions ---


class TestExportDataset:
    """Test full export pipeline with mock contributions."""

    def test_output_directory_structure(self, export_env):
        """Export creates correct directory structure."""
        export_env["make_contribution"]("aaa", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
        ])

        _run_export(export_env)

        out = export_env["output_dir"]
        assert (out / "images" / "train").is_dir()
        assert (out / "images" / "val").is_dir()
        assert (out / "labels" / "train").is_dir()
        assert (out / "labels" / "val").is_dir()
        assert (out / "dataset.yaml").is_file()

    def test_image_and_label_files(self, export_env):
        """Export produces tiled JPEG image and label txt files."""
        export_env["make_contribution"]("abc", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
            {"type": "clivis", "bbox": {"x": 50, "y": 60, "width": 20, "height": 18}},
        ])

        _run_export(export_env, val_ratio=0.0)  # All to train

        out = export_env["output_dir"]
        # 200x300 image with default tile_size=640 → single tile
        img_path = out / "images" / "train" / "abc_tile0_0.jpg"
        lbl_path = out / "labels" / "train" / "abc_tile0_0.txt"

        assert img_path.is_file()
        assert lbl_path.is_file()

        # Verify label content
        lines = lbl_path.read_text().strip().split("\n")
        assert len(lines) == 2

        # First neume: punctum (class 0)
        parts = lines[0].split()
        assert parts[0] == "0"
        assert len(parts) == 5  # class_id xc yc w h

        # Second neume: clivis (class 1)
        parts = lines[1].split()
        assert parts[0] == "1"

    def test_label_values_correct(self, export_env):
        """Label file contains correctly normalized bbox values for tile."""
        # Small image → single tile covering entire image
        export_env["make_contribution"]("xyz", [
            {"type": "punctum", "bbox": {"x": 100, "y": 200, "width": 40, "height": 30}},
        ], img_size=(400, 500))

        _run_export(export_env, val_ratio=0.0)

        lbl_path = export_env["output_dir"] / "labels" / "train" / "xyz_tile0_0.txt"
        line = lbl_path.read_text().strip()
        parts = line.split()

        assert parts[0] == "0"  # punctum
        # Tile is 400x500 (whole image), bbox at (100, 200, 40, 30)
        assert float(parts[1]) == pytest.approx(0.3)     # (100 + 20) / 400
        assert float(parts[2]) == pytest.approx(0.43)    # (200 + 15) / 500
        assert float(parts[3]) == pytest.approx(0.1)     # 40 / 400
        assert float(parts[4]) == pytest.approx(0.06)    # 30 / 500

    def test_dataset_yaml_content(self, export_env):
        """dataset.yaml has correct structure and class names."""
        export_env["make_contribution"]("aaa", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
        ])

        _run_export(export_env)

        yaml_path = export_env["output_dir"] / "dataset.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        assert data["path"] == str(export_env["output_dir"].resolve())
        assert data["train"] == "images/train"
        assert data["val"] == "images/val"
        assert data["names"] == {0: "punctum", 1: "clivis", 2: "podatus"}

    def test_clears_existing_output(self, export_env):
        """Export clears old output directory before writing."""
        out = export_env["output_dir"]
        out.mkdir(parents=True)
        stale = out / "stale_file.txt"
        stale.write_text("old data")

        export_env["make_contribution"]("aaa", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
        ])

        _run_export(export_env)

        assert not stale.exists()
        assert (out / "dataset.yaml").is_file()

    def test_summary_counts_are_tiles(self, export_env):
        """Export summary counts tiles, not contributions."""
        export_env["make_contribution"]("aaa", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
        ])
        export_env["make_contribution"]("bbb", [
            {"type": "clivis", "bbox": {"x": 30, "y": 40, "width": 20, "height": 18}},
        ])
        export_env["make_contribution"]("ccc", [])  # No neumes — skipped

        summary = _run_export(export_env, val_ratio=0.0)

        # Each contribution is a small image (200x300) → 1 tile each
        assert summary["exported"] == 2  # 2 tiles (one per contribution)
        assert summary["skipped"] == 1
        assert summary["train"] == 2
        assert summary["val"] == 0

    def test_large_image_produces_multiple_tiles(self, export_env):
        """A large image with spread-out neumes produces multiple tiles."""
        export_env["make_contribution"]("big", [
            {"type": "punctum", "bbox": {"x": 100, "y": 100, "width": 40, "height": 30}},
            {"type": "clivis", "bbox": {"x": 900, "y": 900, "width": 40, "height": 30}},
        ], img_size=(1200, 1200))

        summary = _run_export(export_env, val_ratio=0.0)

        # tile_size=640 (default, no segmentation lines), overlap=0.2
        # Multiple tiles, at least 2 should contain neumes
        assert summary["exported"] >= 2

        train_imgs = list((export_env["output_dir"] / "images" / "train").iterdir())
        assert all("_tile" in f.name for f in train_imgs)

    def test_tile_naming_convention(self, export_env):
        """Tile files follow {id}_tile{row}_{col} naming."""
        export_env["make_contribution"]("myid", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
        ])

        _run_export(export_env, val_ratio=0.0)

        train_imgs = list((export_env["output_dir"] / "images" / "train").iterdir())
        assert len(train_imgs) == 1
        assert train_imgs[0].name == "myid_tile0_0.jpg"


# --- 5.4 Skip logic ---


class TestSkipLogic:
    """Test contribution skip behavior."""

    def test_skip_no_neumes(self, export_env):
        """Contributions with empty neumes array are skipped."""
        export_env["make_contribution"]("empty", [])

        summary = _run_export(export_env)

        assert summary["exported"] == 0
        assert summary["skipped"] == 1

    def test_skip_all_unknown_types(self, export_env):
        """Contributions where all neume types are unknown are skipped."""
        export_env["make_contribution"]("unknown", [
            {"type": "unknown-type", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
            {"type": "another-unknown", "bbox": {"x": 30, "y": 40, "width": 20, "height": 18}},
        ])

        summary = _run_export(export_env)

        assert summary["exported"] == 0
        assert summary["skipped"] == 1

    def test_mixed_known_unknown_exports_only_known(self, export_env):
        """Mixed contributions export only known-type neumes."""
        export_env["make_contribution"]("mixed", [
            {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
            {"type": "unknown-type", "bbox": {"x": 30, "y": 40, "width": 20, "height": 18}},
            {"type": "clivis", "bbox": {"x": 50, "y": 60, "width": 25, "height": 20}},
        ])

        _run_export(export_env, val_ratio=0.0)

        lbl_path = export_env["output_dir"] / "labels" / "train" / "mixed_tile0_0.txt"
        lines = lbl_path.read_text().strip().split("\n")
        assert len(lines) == 2  # Only punctum and clivis

        class_ids = [line.split()[0] for line in lines]
        assert class_ids == ["0", "1"]  # punctum=0, clivis=1

    def test_no_contributions_returns_zero(self, export_env):
        """Empty contributions directory returns zero counts."""
        summary = _run_export(export_env)

        assert summary["exported"] == 0
        assert summary["skipped"] == 0


# --- 5.5 Train/val split reproducibility ---


class TestTrainValSplit:
    """Test train/val splitting behavior."""

    def test_reproducible_with_same_seed(self, export_env):
        """Same seed produces identical splits."""
        for i in range(5):
            export_env["make_contribution"](f"c{i:03d}", [
                {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
            ])

        summary1 = _run_export(export_env, seed=42, val_ratio=0.4)
        train_files_1 = sorted(
            f.name for f in (export_env["output_dir"] / "images" / "train").iterdir()
        )
        val_files_1 = sorted(
            f.name for f in (export_env["output_dir"] / "images" / "val").iterdir()
        )

        # Run again with same seed
        summary2 = _run_export(export_env, seed=42, val_ratio=0.4)
        train_files_2 = sorted(
            f.name for f in (export_env["output_dir"] / "images" / "train").iterdir()
        )
        val_files_2 = sorted(
            f.name for f in (export_env["output_dir"] / "images" / "val").iterdir()
        )

        assert train_files_1 == train_files_2
        assert val_files_1 == val_files_2
        assert summary1 == summary2

    def test_different_seed_may_differ(self, export_env):
        """Different seeds can produce different splits (with enough data)."""
        for i in range(10):
            export_env["make_contribution"](f"c{i:03d}", [
                {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
            ])

        _run_export(export_env, seed=42, val_ratio=0.3)
        val_1 = sorted(
            f.name for f in (export_env["output_dir"] / "images" / "val").iterdir()
        )

        _run_export(export_env, seed=999, val_ratio=0.3)
        val_2 = sorted(
            f.name for f in (export_env["output_dir"] / "images" / "val").iterdir()
        )

        # With 10 items and different seeds, splits should differ
        # (statistically very likely, not guaranteed)
        assert val_1 != val_2

    def test_default_split_ratio(self, export_env):
        """Default 80/20 split distributes correctly."""
        for i in range(10):
            export_env["make_contribution"](f"c{i:03d}", [
                {"type": "punctum", "bbox": {"x": 10, "y": 20, "width": 15, "height": 12}},
            ])

        summary = _run_export(export_env, val_ratio=0.2)

        # Each small contribution produces 1 tile
        assert summary["train"] == 8
        assert summary["val"] == 2
        assert summary["exported"] == 10


# --- 5.6 Bbox assignment to tiles ---


class TestAssignBboxesToTile:
    """Test bbox-to-tile assignment and clipping."""

    CLASS_MAP = {"punctum": 0, "clivis": 1}

    def test_bbox_center_inside_tile(self):
        """Bbox whose center is inside the tile gets assigned."""
        neumes = [
            {"type": "punctum", "bbox": {"x": 100, "y": 100, "width": 40, "height": 30}},
        ]
        # Center: (120, 115), tile covers [0, 0, 640, 640]
        result = _assign_bboxes_to_tile(neumes, 0, 0, 640, 640, self.CLASS_MAP)
        assert len(result) == 1
        assert result[0].startswith("0 ")

    def test_bbox_center_outside_tile(self):
        """Bbox whose center is outside the tile gets excluded."""
        neumes = [
            {"type": "punctum", "bbox": {"x": 700, "y": 100, "width": 40, "height": 30}},
        ]
        # Center: (720, 115), tile covers [0, 0, 640, 640]
        result = _assign_bboxes_to_tile(neumes, 0, 0, 640, 640, self.CLASS_MAP)
        assert len(result) == 0

    def test_bbox_clipped_to_tile_boundary(self):
        """Bbox extending past tile edge gets clipped."""
        neumes = [
            # Center at (110, 110), but bbox extends from 90 to 150
            {"type": "punctum", "bbox": {"x": 90, "y": 90, "width": 60, "height": 60}},
        ]
        # Tile starts at (100, 100), so left/top should be clipped
        result = _assign_bboxes_to_tile(neumes, 100, 100, 640, 640, self.CLASS_MAP)
        assert len(result) == 1

        parts = result[0].split()
        # Clipped bbox: local (0, 0) to (50, 50) in tile coords
        # YOLO: center=(25/640, 25/640), size=(50/640, 50/640)
        assert float(parts[1]) == pytest.approx(25 / 640, abs=1e-5)
        assert float(parts[2]) == pytest.approx(25 / 640, abs=1e-5)
        assert float(parts[3]) == pytest.approx(50 / 640, abs=1e-5)
        assert float(parts[4]) == pytest.approx(50 / 640, abs=1e-5)

    def test_multiple_neumes_mixed_assignment(self):
        """Only neumes with centers inside the tile are assigned."""
        neumes = [
            {"type": "punctum", "bbox": {"x": 10, "y": 10, "width": 20, "height": 20}},   # center (20, 20) - inside
            {"type": "clivis", "bbox": {"x": 700, "y": 700, "width": 20, "height": 20}},   # center (710, 710) - outside
        ]
        result = _assign_bboxes_to_tile(neumes, 0, 0, 640, 640, self.CLASS_MAP)
        assert len(result) == 1
        assert result[0].startswith("0 ")  # punctum only

    def test_bbox_coords_normalized_to_tile(self):
        """YOLO coords are normalized relative to the tile, not the full image."""
        neumes = [
            {"type": "punctum", "bbox": {"x": 200, "y": 200, "width": 40, "height": 30}},
        ]
        # Tile at (100, 100, 640, 640)
        # Local bbox: x=100, y=100, w=40, h=30
        result = _assign_bboxes_to_tile(neumes, 100, 100, 640, 640, self.CLASS_MAP)
        assert len(result) == 1

        parts = result[0].split()
        assert float(parts[1]) == pytest.approx((100 + 20) / 640, abs=1e-5)  # local x_center
        assert float(parts[2]) == pytest.approx((100 + 15) / 640, abs=1e-5)  # local y_center
        assert float(parts[3]) == pytest.approx(40 / 640, abs=1e-5)
        assert float(parts[4]) == pytest.approx(30 / 640, abs=1e-5)
