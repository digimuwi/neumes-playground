"""Model loading with caching and mtime validation."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kraken.lib import models

logger = logging.getLogger(__name__)

# Model paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"

# Default Tridis model (shipped with the app)
TRIDIS_MODEL_PATH = MODELS_DIR / "Tridis_Medieval_EarlyModern.mlmodel"


@dataclass
class CachedModel:
    """A loaded model with its file modification time."""

    model: models.TorchSeqRecognizer
    mtime: float


# Module-level cache
_text_recognition_cache: Optional[CachedModel] = None


def _load_with_cache(
    path: Path,
    cache: Optional[CachedModel],
) -> tuple[Optional[models.TorchSeqRecognizer], Optional[CachedModel]]:
    """Load a model with caching and mtime validation.

    Args:
        path: Path to the model file
        cache: Existing cache entry (or None)

    Returns:
        Tuple of (model, updated_cache). Model is None if file doesn't exist.
    """
    if not path.exists():
        return None, None

    current_mtime = path.stat().st_mtime

    # Return cached if mtime hasn't changed
    if cache is not None and cache.mtime == current_mtime:
        return cache.model, cache

    # Load fresh
    logger.info(f"Loading model from {path}")
    try:
        model = models.load_any(str(path))
        new_cache = CachedModel(model=model, mtime=current_mtime)
        return model, new_cache
    except Exception:
        logger.exception(f"Failed to load model from {path}")
        return None, None


def load_text_recognition_model() -> Optional[models.TorchSeqRecognizer]:
    """Load the Tridis text recognition model with caching."""
    global _text_recognition_cache

    model, _text_recognition_cache = _load_with_cache(
        TRIDIS_MODEL_PATH, _text_recognition_cache
    )
    return model
