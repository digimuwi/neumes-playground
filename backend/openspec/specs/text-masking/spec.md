### Requirement: Mask text regions from manuscript images
The `mask_text_regions` function SHALL accept a PIL RGB image and a Kraken `Segmentation` object and SHALL return a new PIL RGB image with all text boundary polygons filled with locally-sampled parchment color. The input image SHALL NOT be modified.

#### Scenario: Text regions are filled with local parchment color
- **WHEN** `mask_text_regions` is called with an image containing text lines and a segmentation with boundary polygons
- **THEN** each boundary polygon region in the returned image is filled with a solid color matching the surrounding parchment
- **AND** pixels outside all boundary polygons are unchanged from the input image

#### Scenario: Input image is not modified
- **WHEN** `mask_text_regions` is called with an image and segmentation
- **THEN** the original image pixel data is unchanged after the call

### Requirement: Sample fill color from parchment adjacent to each polygon
For each text boundary polygon, the fill color SHALL be computed by dilating the polygon slightly, sampling pixel colors in the ring between the original and dilated boundary, and taking the per-channel median. This produces a fill color that matches the local parchment tone.

#### Scenario: Fill color matches local parchment around each polygon
- **WHEN** an image has regions of different parchment color (e.g., darker at top, lighter at bottom)
- **THEN** each masked polygon is filled with a color sampled from its own surrounding parchment, not a global average

#### Scenario: Sampling ring near image edge
- **WHEN** a boundary polygon is near the image edge and the dilated polygon extends beyond the image boundary
- **THEN** the sampling ring is clipped to the image bounds
- **AND** the fill color is still computed from the available ring pixels

### Requirement: Handle images with no detected lines
When the segmentation contains zero lines, `mask_text_regions` SHALL return a copy of the input image unchanged.

#### Scenario: Zero lines in segmentation
- **WHEN** `mask_text_regions` is called with a segmentation that has an empty `lines` list
- **THEN** the returned image is identical to the input image

### Requirement: Handle lines with missing or empty boundary polygons
If a line in the segmentation has no boundary polygon (empty list or None), that line SHALL be skipped without error.

#### Scenario: Line with no boundary polygon
- **WHEN** a segmentation line has an empty or missing `boundary` field
- **THEN** that line is skipped and the image is not modified for that line
- **AND** other lines with valid boundaries are still masked normally

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
