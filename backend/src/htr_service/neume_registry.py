"""Shared neume class registry backed by YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models.types import NeumeClass, NeumeClassCreate, NeumeClassUpdate

BASE_DIR = Path(__file__).parent.parent.parent
DEFAULT_CLASSES_PATH = BASE_DIR / "neume_classes.yaml"

LEGACY_DETAILS: dict[str, tuple[str, str]] = {
    "punctum": ("Punctum", "Single note (dot)"),
    "virga": ("Virga", "Single note with stem"),
    "pes": ("Pes", "Two notes ascending"),
    "clivis": ("Clivis", "Two notes descending"),
    "torculus": ("Torculus", "Three notes: low-high-low"),
    "porrectus": ("Porrectus", "Three notes: high-low-high"),
    "scandicus": ("Scandicus", "Three notes ascending"),
    "climacus": ("Climacus", "Three+ notes descending"),
    "pes subbipunctis": ("Pes Subbipunctis", "Pes followed by two descending puncta"),
    "pes subtripunctis": ("Pes Subtripunctis", "Pes followed by three descending puncta"),
    "pes praebipunctis": ("Pes Praebipunctis", "Two ascending puncta preceding a pes"),
    "scandicus flexus": ("Scandicus Flexus", "Scandicus with descending final note"),
    "torculus resupinus": ("Torculus Resupinus", "Torculus with ascending final note"),
    "porrectus flexus": ("Porrectus Flexus", "Porrectus with descending final note"),
    "scandicus climacus": ("Scandicus Climacus", "Ascending then descending notes (scandicus + climacus)"),
    "bivirga": ("Bivirga", "Two virgae on same pitch"),
    "trivirga": ("Trivirga", "Three virgae on same pitch"),
    "stropha": ("Stropha", "Repeated note with special articulation"),
    "bistropha": ("Bistropha", "Two strophae"),
    "tristropha": ("Tristropha", "Three strophae"),
    "pressus": ("Pressus", "Compound neume with held note"),
    "uncinus": ("Uncinus", "Hook-shaped neume"),
    "celeriter": ("Celeriter", "Quick descending-ascending figure"),
    "quilisma": ("Quilisma", "Ornamental neume"),
    "salicus": ("Salicus", "Ascending with rhythmic marking"),
    "apostropha": ("Apostropha", "Liquescent note"),
    "virga episema": ("Virga episema", "Single note with stem, with episema"),
    "clivis episema": ("Clivis episema", "Two notes descending, with episema"),
    "clivis episema praebipunctis": ("Clivis Episema Praebipunctis", "Two ascending puncta preceding a clivis with episema"),
    "climacus episema": ("Climacus episema", "Three+ notes descending, with episema"),
    "apostropha episema": ("Apostropha episema", "Liquescent note, with episema"),
    "oriscus": ("Oriscus", "Ornamental wavy note"),
    "trigon": ("Trigon", "Triangular-shaped note"),
    "pes liquescens": ("Pes Liquescens", "Ascending two-note neume with liquescent ending"),
    "torculus liquescens": ("Torculus Liquescens", "Low-high-low neume with liquescent ending"),
    "pes quadratus": ("Pes Quadratus", "Ascending two-note neume with square form"),
    "pes quadratus subbipunctis": ("Pes Quadratus Subbipunctis", "Pes quadratus followed by two descending puncta"),
    "tenete": ("Tenete", "Held/sustained note indication"),
    "porrectus subbipunctis": ("Porrectus Subbipunctis", "Porrectus followed by two descending puncta"),
    "expectate": ("Expectate", "Extended concluding neume formula"),
    "cephalicus": ("Cephalicus", "Liquescent descending neume"),
    "equaliter": ("Equaliter", "Repeated equal-pitch motion"),
    "inferius": ("Inferius", "Lower auxiliary neume"),
    "levare": ("Levare", "Rising preparatory neume"),
    "mediocriter": ("Mediocriter", "Moderately inflected neume"),
    "pressionem": ("Pressionem", "Pressing/emphatic compound neume"),
    "sursum": ("Sursum", "Upward-directed auxiliary neume"),
    "podatus": ("Podatus", "Two notes ascending"),
}


def _normalize_key(value: str) -> str:
    return " ".join(value.strip().split()).lower()


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def _default_name(key: str) -> str:
    legacy = LEGACY_DETAILS.get(key)
    if legacy:
        return legacy[0]
    return " ".join(part.capitalize() for part in key.split())


def _default_description(key: str) -> str:
    legacy = LEGACY_DETAILS.get(key)
    return legacy[1] if legacy else ""


def _load_raw_yaml(path: Path | None) -> dict:
    path = path or DEFAULT_CLASSES_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"Neume class mapping file not found: {path}\n"
            "Create neume_classes.yaml with a 'classes' list."
        )

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "classes" not in data:
        got = list(data.keys()) if isinstance(data, dict) else type(data)
        raise ValueError(f"Invalid neume_classes.yaml: expected 'classes' key, got {got}")

    if not isinstance(data["classes"], list):
        raise ValueError(
            f"Invalid neume_classes.yaml: 'classes' must be a list, got {type(data['classes'])}"
        )

    return data


def load_neume_registry(path: Path | None = None) -> list[NeumeClass]:
    """Load the shared neume class registry.

    Supports the legacy flat string list as well as the structured object list.
    """
    data = _load_raw_yaml(path)
    raw_classes = data["classes"]
    classes: list[NeumeClass] = []

    for idx, entry in enumerate(raw_classes):
        if isinstance(entry, str):
            key = _normalize_key(entry)
            classes.append(
                NeumeClass(
                    id=idx,
                    key=key,
                    name=_default_name(key),
                    description=_default_description(key),
                    active=True,
                )
            )
            continue

        if not isinstance(entry, dict):
            raise ValueError(f"Invalid neume_classes.yaml entry at index {idx}: {type(entry)}")

        raw_key = entry.get("key")
        if not isinstance(raw_key, str) or not raw_key.strip():
            raise ValueError(f"Invalid neume_classes.yaml entry at index {idx}: missing non-empty key")

        key = _normalize_key(raw_key)
        name = entry.get("name")
        description = entry.get("description", "")
        raw_id = entry.get("id", idx)
        active = entry.get("active", True)

        if not isinstance(raw_id, int) or raw_id < 0:
            raise ValueError(f"Invalid neume_classes.yaml entry for {key!r}: id must be a non-negative integer")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise ValueError(f"Invalid neume_classes.yaml entry for {key!r}: name must be a non-empty string")
        if not isinstance(description, str):
            raise ValueError(f"Invalid neume_classes.yaml entry for {key!r}: description must be a string")
        if not isinstance(active, bool):
            raise ValueError(f"Invalid neume_classes.yaml entry for {key!r}: active must be a boolean")

        classes.append(
            NeumeClass(
                id=raw_id,
                key=key,
                name=_normalize_name(name) if isinstance(name, str) else _default_name(key),
                description=description.strip(),
                active=active,
            )
        )

    _validate_registry(classes)
    return sorted(classes, key=lambda item: item.id)


def _validate_registry(classes: list[NeumeClass]) -> None:
    seen_ids: set[int] = set()
    seen_keys: set[str] = set()
    seen_names: set[str] = set()

    for neume_class in classes:
        if neume_class.id in seen_ids:
            raise ValueError(f"Duplicate neume class id: {neume_class.id}")
        if neume_class.key in seen_keys:
            raise ValueError(f"Duplicate neume class key: {neume_class.key}")

        lowered_name = neume_class.name.casefold()
        if lowered_name in seen_names:
            raise ValueError(f"Duplicate neume class name: {neume_class.name}")

        seen_ids.add(neume_class.id)
        seen_keys.add(neume_class.key)
        seen_names.add(lowered_name)


def save_neume_registry(classes: list[NeumeClass], path: Path | None = None) -> None:
    """Persist the shared neume class registry in structured form."""
    path = path or DEFAULT_CLASSES_PATH
    ordered = sorted(classes, key=lambda item: item.id)
    _validate_registry(ordered)

    data = {
        "classes": [
            {
                "id": neume_class.id,
                "key": neume_class.key,
                "name": neume_class.name,
                "description": neume_class.description,
                "active": neume_class.active,
            }
            for neume_class in ordered
        ]
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=False)


def load_neume_class_map(path: Path | None = None) -> dict[str, int]:
    """Load the canonical key -> stable integer ID mapping for YOLO export."""
    return {neume_class.key: neume_class.id for neume_class in load_neume_registry(path)}


def create_neume_class(
    payload: NeumeClassCreate,
    path: Path | None = None,
) -> NeumeClass:
    """Append a new class to the shared registry."""
    classes = load_neume_registry(path)
    key = _normalize_key(payload.key)
    name = _normalize_name(payload.name)

    if any(existing.key == key for existing in classes):
        raise ValueError(f"Neume class key already exists: {key}")
    if any(existing.name.casefold() == name.casefold() for existing in classes):
        raise ValueError(f"Neume class name already exists: {name}")

    next_id = max((existing.id for existing in classes), default=-1) + 1
    new_class = NeumeClass(
        id=next_id,
        key=key,
        name=name,
        description=payload.description.strip(),
        active=True,
    )
    classes.append(new_class)
    save_neume_registry(classes, path)
    return new_class


def update_neume_class(
    class_id: int,
    payload: NeumeClassUpdate,
    path: Path | None = None,
) -> NeumeClass:
    """Update mutable fields of an existing neume class."""
    classes = load_neume_registry(path)
    index = next((idx for idx, entry in enumerate(classes) if entry.id == class_id), -1)
    if index == -1:
        raise KeyError(class_id)

    current = classes[index]
    name = _normalize_name(payload.name) if payload.name is not None else current.name
    description = payload.description.strip() if payload.description is not None else current.description
    active = payload.active if payload.active is not None else current.active

    for other in classes:
        if other.id == class_id:
            continue
        if other.name.casefold() == name.casefold():
            raise ValueError(f"Neume class name already exists: {name}")

    updated = NeumeClass(
        id=current.id,
        key=current.key,
        name=name,
        description=description,
        active=active,
    )
    classes[index] = updated
    save_neume_registry(classes, path)
    return updated
