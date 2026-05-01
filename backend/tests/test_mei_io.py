"""Tests for MEI 5.0 reader/writer.

Validates that:
- All fixtures in spec/fixtures/ parse without error
- Parser correctly reads all spec conventions (orphans, polygons, wordpos)
- Writer is deterministic and idempotent (canonical output)
- Semantic round-trip preserves the contribution model
"""

from pathlib import Path

import pytest

from htr_service.contribution.mei_io import (
    ContributionDocument,
    canonicalize_mei,
    read_contribution,
    relabel_neume_in_mei,
    write_contribution,
)
from htr_service.models.types import (
    BBox,
    ImageMetadata,
    LineInput,
    NeumeInput,
    SyllableInput,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "spec" / "fixtures"

ALL_FIXTURES = sorted(FIXTURES_DIR.glob("*.mei"))


# --- Fixture-driven smoke tests ---


@pytest.mark.parametrize("fixture_path", ALL_FIXTURES, ids=lambda p: p.name)
def test_fixture_parses(fixture_path: Path):
    """Every fixture parses without raising."""
    doc = read_contribution(fixture_path.read_bytes())
    assert isinstance(doc, ContributionDocument)


@pytest.mark.parametrize("fixture_path", ALL_FIXTURES, ids=lambda p: p.name)
def test_writer_idempotent(fixture_path: Path):
    """Writing twice through the canonical pipeline gives identical bytes."""
    once = canonicalize_mei(fixture_path.read_bytes())
    twice = canonicalize_mei(once)
    assert once == twice


@pytest.mark.parametrize("fixture_path", ALL_FIXTURES, ids=lambda p: p.name)
def test_semantic_round_trip(fixture_path: Path):
    """Parse → serialize → parse yields the same model."""
    a = read_contribution(fixture_path.read_bytes())
    b = read_contribution(write_contribution(a))
    assert a.model_dump() == b.model_dump()


# --- Per-fixture assertions ---


def _load(name: str) -> ContributionDocument:
    return read_contribution((FIXTURES_DIR / name).read_bytes())


def test_simple_line_fixture():
    """01_simple_line: 1 line, 1 syllable 'Te' wordpos=s, 1 punctum."""
    doc = _load("01_simple_line.mei")
    assert doc.image == ImageMetadata(filename="image.jpg", width=200, height=300)
    assert len(doc.lines) == 1
    assert len(doc.lines[0].syllables) == 1
    assert doc.lines[0].syllables[0].text == "Te"  # wordpos=s, no hyphen
    assert len(doc.neumes) == 1
    assert doc.neumes[0].type == "punctum"
    # Neume bbox: rect at (15,30)-(35,48) → x=15, y=30, w=20, h=18
    assert doc.neumes[0].bbox == BBox(x=15, y=30, width=20, height=18)


def test_hyphenated_multi_line_fixture():
    """02_hyphenated_multi_line: 2 lines, 5 syllables with hyphen reconstruction."""
    doc = _load("02_hyphenated_multi_line.mei")
    assert len(doc.lines) == 2
    line1_texts = [s.text for s in doc.lines[0].syllables]
    line2_texts = [s.text for s in doc.lines[1].syllables]
    assert line1_texts == ["Do-", "mi-", "ne"]  # i, m, t reconstructed
    assert line2_texts == ["san-", "ctus"]  # i, t
    assert len(doc.neumes) == 5


def test_orphan_neumes_fixture():
    """03_orphan_neumes: per-line orphan carrier with 2 orphan neumes."""
    doc = _load("03_orphan_neumes.mei")
    assert len(doc.lines) == 1
    # The "Te" syllable is the only real syllable
    assert len(doc.lines[0].syllables) == 1
    assert doc.lines[0].syllables[0].text == "Te"
    # 3 neumes total: 1 assigned to "Te" + 2 orphans, all flat
    assert len(doc.neumes) == 3
    types = sorted(n.type for n in doc.neumes)
    assert types == ["clivis", "punctum", "virga"]


def test_no_neumes_fixture():
    """04_no_neumes: 3 syllables, no neumes."""
    doc = _load("04_no_neumes.mei")
    assert len(doc.lines) == 1
    assert [s.text for s in doc.lines[0].syllables] == ["Pa-", "ter-", "noster"]
    assert doc.neumes == []


def test_no_syllables_fixture():
    """05_no_syllables: synthetic global line, 2 orphan neumes, no real lines."""
    doc = _load("05_no_syllables.mei")
    # Synthetic line is dropped on read
    assert doc.lines == []
    assert len(doc.neumes) == 2
    assert {n.type for n in doc.neumes} == {"punctum", "clivis"}


def test_polygonal_boundary_fixture():
    """06_polygonal_boundary: syllable polygons with non-rect shape preserved."""
    doc = _load("06_polygonal_boundary.mei")
    assert len(doc.lines) == 1
    assert len(doc.lines[0].syllables) == 3
    # First syllable polygon should have 4 distinct (non-collinear) points
    poly = doc.lines[0].syllables[0].boundary
    assert len(poly) == 4
    # Verify it's not just an axis-aligned rect
    xs = {pt[0] for pt in poly}
    ys = {pt[1] for pt in poly}
    # Non-rect: the y-coordinates should not collapse to just two values
    assert len(ys) > 2 or len(xs) > 2


# --- Writer determinism ---


def test_writer_produces_deterministic_output():
    """Building the same model twice gives identical bytes."""
    doc = ContributionDocument(
        image=ImageMetadata(filename="image.jpg", width=100, height=100),
        lines=[
            LineInput(
                boundary=[[0, 50], [100, 50], [100, 80], [0, 80]],
                syllables=[
                    SyllableInput(
                        text="Hi", boundary=[[0, 50], [50, 50], [50, 80], [0, 80]]
                    ),
                ],
            )
        ],
        neumes=[
            NeumeInput(
                type="punctum",
                bbox=BBox(x=10, y=20, width=15, height=15),
            ),
        ],
    )
    a = write_contribution(doc)
    b = write_contribution(doc)
    assert a == b


def test_writer_produces_xml_declaration_and_namespace():
    """Output has XML declaration and MEI namespace on root."""
    doc = ContributionDocument(
        image=ImageMetadata(filename="x.jpg", width=10, height=10),
        lines=[],
        neumes=[],
    )
    out = write_contribution(doc).decode("utf-8")
    assert out.startswith("<?xml version='1.0' encoding='UTF-8'?>\n")
    assert 'xmlns="http://www.music-encoding.org/ns/mei"' in out
    assert 'meiversion="5.0"' in out


# --- Relabel ---


def test_relabel_neume_changes_type():
    """relabel_neume_in_mei finds by bbox and updates type."""
    fixture_bytes = (FIXTURES_DIR / "01_simple_line.mei").read_bytes()
    canonical = canonicalize_mei(fixture_bytes)
    new_bytes = relabel_neume_in_mei(
        canonical, {"x": 15, "y": 30, "width": 20, "height": 18}, "clivis"
    )
    doc = read_contribution(new_bytes)
    assert doc.neumes[0].type == "clivis"


def test_relabel_neume_missing_raises():
    """Relabel with non-matching bbox raises ValueError."""
    fixture_bytes = (FIXTURES_DIR / "01_simple_line.mei").read_bytes()
    with pytest.raises(ValueError, match="No neume found"):
        relabel_neume_in_mei(
            fixture_bytes,
            {"x": 999, "y": 999, "width": 1, "height": 1},
            "clivis",
        )


# --- Empty contribution ---


def test_empty_contribution_round_trip():
    """A contribution with no lines and no neumes round-trips cleanly."""
    doc = ContributionDocument(
        image=ImageMetadata(filename="img.jpg", width=100, height=100),
        lines=[],
        neumes=[],
    )
    out = write_contribution(doc)
    parsed = read_contribution(out)
    assert parsed.model_dump() == doc.model_dump()
