"""Character bounding box extraction from Kraken cuts."""

from typing import NamedTuple


class CharBBox(NamedTuple):
    """Bounding box for a single character."""

    x: int
    y: int
    width: int
    height: int
    char: str
    confidence: float


def extract_char_bboxes(
    text: str, cuts: list[tuple], confidences: list[float]
) -> list[CharBBox]:
    """Extract character bounding boxes from Kraken cuts.

    Kraken cuts are position markers along the baseline for each character.
    Each cut is a 4-point polygon representing a vertical line at the character's
    position. The character's bounding box spans from the current cut's x-position
    to the next cut's x-position.

    Args:
        text: Recognized text string
        cuts: List of cut polygons (4 points each)
        confidences: List of confidence scores per character

    Returns:
        List of CharBBox, one per character
    """
    if len(text) != len(cuts) or len(text) != len(confidences):
        raise ValueError(
            f"Length mismatch: text={len(text)}, cuts={len(cuts)}, "
            f"confidences={len(confidences)}"
        )

    if not cuts:
        return []

    bboxes = []

    for i, (char, cut, conf) in enumerate(zip(text, cuts, confidences)):
        # Get x position from current cut (use min x of all points for robustness)
        x_values = [pt[0] for pt in cut]
        x_left = min(x_values)

        # Get x position from next cut, or estimate for last char
        if i < len(cuts) - 1:
            next_cut_x_values = [pt[0] for pt in cuts[i + 1]]
            x_right = min(next_cut_x_values)
        else:
            # Estimate last character width based on average or fixed value
            avg_width = _estimate_avg_char_width(cuts)
            x_right = x_left + avg_width

        # Get y extent from current cut points
        y_values = [pt[1] for pt in cut]
        y_top = min(y_values)
        y_bottom = max(y_values)

        bboxes.append(
            CharBBox(
                x=x_left,
                y=y_top,
                width=max(1, x_right - x_left),
                height=max(1, y_bottom - y_top),
                char=char,
                confidence=conf,
            )
        )

    return bboxes


def _estimate_avg_char_width(cuts: list[tuple]) -> int:
    """Estimate average character width from cuts."""
    if len(cuts) < 2:
        return 30  # Default fallback

    widths = []
    for i in range(len(cuts) - 1):
        current_x = min(pt[0] for pt in cuts[i])
        next_x = min(pt[0] for pt in cuts[i + 1])
        width = next_x - current_x
        if width > 0:
            widths.append(width)

    if widths:
        return int(sum(widths) / len(widths))
    return 30
