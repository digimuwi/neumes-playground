"""Latin syllabification using pyphen with ecclesiastical Latin patterns."""

from pathlib import Path
from typing import NamedTuple

import pyphen

from ..pipeline.geometry import CharBBox


class SyllableResult(NamedTuple):
    """A syllable with its bounding box and metadata."""

    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    line_index: int


# Module-level syllabifier cache
_syllabifier = None
_dict_path = None


def load_syllabifier(dict_path: Path) -> pyphen.Pyphen:
    """Load the Latin syllabifier with caching."""
    global _syllabifier, _dict_path

    if _syllabifier is None or _dict_path != dict_path:
        _syllabifier = pyphen.Pyphen(filename=str(dict_path))
        _dict_path = dict_path

    return _syllabifier


def syllabify_word(word: str, syllabifier: pyphen.Pyphen) -> list[str]:
    """Split a word into syllables with trailing hyphens for word continuity.

    Non-final syllables include a trailing hyphen to indicate the word continues.
    Final syllables and single-syllable words have no trailing hyphen.

    Args:
        word: Word to syllabify
        syllabifier: pyphen Pyphen instance

    Returns:
        List of syllables (non-final syllables have trailing hyphens)
    """
    if not word:
        return []

    hyphenated = syllabifier.inserted(word, hyphen="-")
    syllables = hyphenated.split("-")
    # Add trailing hyphen to all but the last syllable
    return [s + "-" for s in syllables[:-1]] + syllables[-1:]


def syllabify_text(text: str, syllabifier: pyphen.Pyphen) -> list[list[str]]:
    """Split text into syllables, preserving word structure.

    Args:
        text: Text to syllabify (may contain spaces)
        syllabifier: pyphen Pyphen instance

    Returns:
        List of lists, where each inner list contains syllables for one word
    """
    words = text.split()
    return [syllabify_word(word, syllabifier) for word in words]


def map_chars_to_syllables(
    text: str, char_bboxes: list[CharBBox], syllabifier: pyphen.Pyphen
) -> list[tuple[str, list[CharBBox]]]:
    """Map characters to syllables with their bounding boxes.

    Args:
        text: Full text string
        char_bboxes: List of CharBBox, one per character in text
        syllabifier: pyphen Pyphen instance

    Returns:
        List of (syllable_text, char_bboxes) tuples
    """
    if len(text) != len(char_bboxes):
        raise ValueError(
            f"Text length ({len(text)}) != char_bboxes length ({len(char_bboxes)})"
        )

    result = []
    char_idx = 0
    words = text.split()

    for word in words:
        # Skip spaces
        while char_idx < len(text) and text[char_idx] == " ":
            char_idx += 1

        # Syllabify the word
        syllables = syllabify_word(word, syllabifier)

        for syllable in syllables:
            if not syllable:
                continue

            # Get the syllable length without trailing hyphen (hyphen is not in original text)
            syllable_len = len(syllable.rstrip("-"))

            # Collect char bboxes for this syllable
            syl_bboxes = []
            for _ in range(syllable_len):
                if char_idx < len(char_bboxes):
                    syl_bboxes.append(char_bboxes[char_idx])
                char_idx += 1

            result.append((syllable, syl_bboxes))

    return result


def merge_char_bboxes(char_bboxes: list[CharBBox]) -> tuple[int, int, int, int, float]:
    """Merge multiple character bboxes into a single bounding box.

    Args:
        char_bboxes: List of CharBBox to merge

    Returns:
        Tuple of (x, y, width, height, avg_confidence)
    """
    if not char_bboxes:
        raise ValueError("Cannot merge empty bbox list")

    x_min = min(b.x for b in char_bboxes)
    y_min = min(b.y for b in char_bboxes)
    x_max = max(b.x + b.width for b in char_bboxes)
    y_max = max(b.y + b.height for b in char_bboxes)
    avg_conf = sum(b.confidence for b in char_bboxes) / len(char_bboxes)

    return (x_min, y_min, x_max - x_min, y_max - y_min, avg_conf)


def process_line_to_syllables(
    text: str,
    char_bboxes: list[CharBBox],
    syllabifier: pyphen.Pyphen,
    line_index: int,
) -> list[SyllableResult]:
    """Process a line of text into syllable results.

    Args:
        text: Line text
        char_bboxes: Character bounding boxes
        syllabifier: pyphen Pyphen instance
        line_index: Index of the line in the document

    Returns:
        List of SyllableResult
    """
    mapped = map_chars_to_syllables(text, char_bboxes, syllabifier)

    results = []
    for syllable_text, syl_char_bboxes in mapped:
        if not syl_char_bboxes:
            continue

        x, y, width, height, confidence = merge_char_bboxes(syl_char_bboxes)
        results.append(
            SyllableResult(
                text=syllable_text,
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=confidence,
                line_index=line_index,
            )
        )

    return results
