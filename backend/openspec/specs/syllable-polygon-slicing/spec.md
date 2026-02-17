### Requirement: Slice a line boundary polygon into per-syllable polygons

The system SHALL provide a function that takes a line boundary polygon (list of `(x, y)` coordinate tuples) and a list of syllable x-ranges (each a `(x_left, x_right)` tuple), and returns a list of polygon coordinate lists — one per syllable.

Each syllable polygon SHALL be computed by intersecting the line boundary polygon with a vertical strip spanning the syllable's x-range across the full image height.

The function SHALL use Shapely for the geometric intersection.

#### Scenario: Line with multiple syllables
- **WHEN** a line boundary polygon and 3 syllable x-ranges are provided
- **THEN** 3 syllable polygons are returned, each following the line's contour but clipped to its syllable's horizontal extent

#### Scenario: Single-syllable line
- **WHEN** a line boundary polygon and 1 syllable x-range spanning the full line width are provided
- **THEN** 1 polygon is returned that matches (approximately) the original line boundary

### Requirement: Handle degenerate intersection results

When Shapely intersection produces a `MultiPolygon`, `GeometryCollection`, or other non-simple result, the function SHALL extract the largest polygon by area. When the intersection produces an empty geometry, the function SHALL skip that syllable and log a warning.

#### Scenario: Intersection produces MultiPolygon
- **WHEN** the intersection of a line polygon and syllable strip produces a MultiPolygon
- **THEN** the largest polygon by area is used as the syllable polygon

#### Scenario: Intersection produces empty geometry
- **WHEN** the intersection of a line polygon and syllable strip produces an empty geometry
- **THEN** that syllable is skipped (no polygon returned for it) and a warning is logged

### Requirement: Derive syllable x-ranges from character cuts

The system SHALL provide a function that takes character cut positions (as produced by Kraken OCR) and a list of syllable character spans (start index, end index), and returns the x-range `(x_left, x_right)` for each syllable.

For the first syllable in a line, `x_left` SHALL be 0 (or the leftmost x of the line polygon). For the last syllable, `x_right` SHALL be the image width (or the rightmost x of the line polygon). This ensures edge syllables are not clipped short.

#### Scenario: Derive x-ranges for 3 syllables from cuts
- **WHEN** a line has 7 characters with cuts at x-positions `[10, 30, 50, 60, 80, 100, 120]` and syllables span characters `[0:2]`, `[2:5]`, `[5:7]`
- **THEN** x-ranges are approximately `(0, 50)`, `(50, 100)`, `(100, image_width)` using the cut x-positions as boundaries

### Requirement: Output polygons as coordinate lists

Each syllable polygon SHALL be returned as a list of `(x, y)` integer tuples suitable for direct JSON serialization and for use with PIL/Shapely polygon operations.

#### Scenario: Polygon coordinate format
- **WHEN** a syllable polygon is computed
- **THEN** it is a list of `(int, int)` tuples representing the polygon vertices in order
