"""Region cropping and coordinate transformation."""

from typing import NamedTuple

from PIL import Image


class Region(NamedTuple):
    """A rectangular region in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int


def crop_to_region(image: Image.Image, region: Region) -> Image.Image:
    """Crop an image to a specified region.

    Args:
        image: PIL Image to crop
        region: Region to extract

    Returns:
        Cropped PIL Image
    """
    left = region.x
    top = region.y
    right = region.x + region.width
    bottom = region.y + region.height

    return image.crop((left, top, right, bottom))


def transform_bbox_to_full_image(
    bbox_x: int, bbox_y: int, bbox_width: int, bbox_height: int, region: Region
) -> tuple[int, int, int, int]:
    """Transform a bounding box from region coordinates to full image coordinates.

    Args:
        bbox_x, bbox_y, bbox_width, bbox_height: Bbox in region-local coords
        region: The region that was cropped from the full image

    Returns:
        Tuple of (x, y, width, height) in full image coordinates
    """
    return (
        bbox_x + region.x,
        bbox_y + region.y,
        bbox_width,
        bbox_height,
    )


def validate_region(image: Image.Image, region: Region) -> None:
    """Validate that a region is within image bounds.

    Args:
        image: PIL Image
        region: Region to validate

    Raises:
        ValueError: If region is outside image bounds
    """
    img_width, img_height = image.size

    if region.x < 0 or region.y < 0:
        raise ValueError(f"Region origin cannot be negative: ({region.x}, {region.y})")

    if region.x + region.width > img_width:
        raise ValueError(
            f"Region exceeds image width: {region.x + region.width} > {img_width}"
        )

    if region.y + region.height > img_height:
        raise ValueError(
            f"Region exceeds image height: {region.y + region.height} > {img_height}"
        )

    if region.width <= 0 or region.height <= 0:
        raise ValueError(
            f"Region dimensions must be positive: {region.width}x{region.height}"
        )
