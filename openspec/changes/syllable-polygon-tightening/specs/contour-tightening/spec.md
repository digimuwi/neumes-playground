## ADDED Requirements

### Requirement: Column-scan produces contour polygon from foreground pixels

The system SHALL produce a contour polygon by scanning vertical columns across the tightened bounding box of a region. For each column (4 pixels wide), the system SHALL record the topmost and bottommost foreground pixel positions. The top-edge points (left-to-right) and bottom-edge points (right-to-left) SHALL be connected into a single closed polygon.

#### Scenario: Standard syllable produces contour polygon
- **WHEN** a region contains foreground pixels spanning multiple columns
- **THEN** the system produces a polygon where the top edge follows the highest ink pixel per column and the bottom edge follows the lowest ink pixel per column

#### Scenario: Empty columns are skipped
- **WHEN** a vertical column within the region contains no foreground pixels (gap between strokes)
- **THEN** that column is skipped and the polygon bridges from the nearest non-empty column on each side

#### Scenario: Polygon uses normalized coordinates
- **WHEN** the column-scan contour is computed from pixel data
- **THEN** the resulting polygon coordinates are normalized to the 0-1 range relative to image dimensions

### Requirement: Contour polygon is simplified with Douglas-Peucker

The system SHALL apply Douglas-Peucker line simplification to the raw column-scan polygon to reduce vertex count. The simplification tolerance SHALL be 2 pixels (converted to normalized coordinates based on image dimensions).

#### Scenario: Collinear points are removed
- **WHEN** the raw column-scan polygon contains a sequence of near-collinear points along a straight top or bottom edge
- **THEN** the simplified polygon removes intermediate points, keeping only the endpoints of the straight segment

#### Scenario: Significant contour changes are preserved
- **WHEN** the raw polygon has a sharp indent or protrusion (e.g., ascender or descender)
- **THEN** the simplified polygon preserves the vertex at the extremity of the indent/protrusion

#### Scenario: Simplified polygon has fewer vertices than raw
- **WHEN** Douglas-Peucker simplification is applied to a raw column-scan polygon
- **THEN** the resulting polygon has equal or fewer vertices than the input

### Requirement: Fallback to rectangular tightening for small regions

The system SHALL fall back to rectangular tightening (producing a 4-point polygon) when the foreground content spans fewer than 2 non-empty columns. This ensures very small annotations remain well-formed.

#### Scenario: Single-column content produces rectangle
- **WHEN** a user draws a rectangle around content that spans only 1 column (< 8 pixels wide of foreground)
- **THEN** the system produces a standard 4-point rectangular polygon via existing tightening

#### Scenario: Multi-column content produces contour polygon
- **WHEN** a user draws a rectangle around content that spans 2 or more non-empty columns
- **THEN** the system produces a contour polygon via the column-scan algorithm

### Requirement: Contour polygon includes padding

The system SHALL include 1 pixel of padding around the detected foreground when computing per-column top and bottom positions. The padding SHALL be clamped to the original user-drawn rectangle bounds.

#### Scenario: Padding expands contour slightly
- **WHEN** the topmost foreground pixel in a column is at pixel row 50
- **THEN** the contour top point for that column uses pixel row 49 (1px padding above)

#### Scenario: Padding clamped to original bounds
- **WHEN** the topmost foreground pixel in a column is at the top edge of the user-drawn rectangle
- **THEN** the contour top point is clamped to the rectangle boundary (no expansion beyond the drawn area)
