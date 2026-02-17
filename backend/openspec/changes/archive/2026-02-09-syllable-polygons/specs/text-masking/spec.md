## ADDED Requirements

### Requirement: Mask arbitrary polygon regions from manuscript images

The system SHALL provide a `mask_polygon_regions` function that accepts a PIL RGB image and a list of polygon coordinate lists (each polygon is a list of `(x, y)` tuples), and SHALL return a new PIL RGB image with all specified polygon regions filled with locally-sampled parchment color. The input image SHALL NOT be modified.

The color sampling strategy SHALL be identical to the existing `mask_text_regions` function: dilate each polygon, sample from the ring, use per-channel median.

#### Scenario: Mask syllable polygons from annotations
- **WHEN** `mask_polygon_regions` is called with an image and a list of syllable boundary polygons extracted from a contribution's annotations
- **THEN** each polygon region in the returned image is filled with locally-sampled parchment color
- **AND** pixels outside all polygons are unchanged

#### Scenario: Empty polygon list
- **WHEN** `mask_polygon_regions` is called with an empty list of polygons
- **THEN** the returned image is identical to the input image

#### Scenario: Input image is not modified
- **WHEN** `mask_polygon_regions` is called
- **THEN** the original image pixel data is unchanged after the call
