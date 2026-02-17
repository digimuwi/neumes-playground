## ADDED Requirements

### Requirement: Annotations use polygon geometry

Every annotation SHALL store its geometry as a `polygon: number[][]` field containing an array of `[x, y]` coordinate pairs in normalized (0-1) coordinates. The `rect: Rectangle` field SHALL NOT exist on annotations.

#### Scenario: OCR syllable annotation has polygon from backend
- **WHEN** the backend returns a syllable with `boundary: [[100,200],[300,200],[300,250],[100,250]]` on a 1000x500 image
- **THEN** the annotation stores `polygon: [[0.1,0.4],[0.3,0.4],[0.3,0.5],[0.1,0.5]]`

#### Scenario: OCR neume annotation converts bbox to polygon
- **WHEN** the backend returns a neume with `bbox: {x:100, y:50, width:40, height:30}` on a 1000x500 image
- **THEN** the annotation stores `polygon: [[0.1,0.1],[0.14,0.1],[0.14,0.16],[0.1,0.16]]`

#### Scenario: User-drawn rectangle becomes 4-point polygon
- **WHEN** the user draws a rectangle from (0.2, 0.3) to (0.5, 0.6)
- **THEN** the annotation stores `polygon: [[0.2,0.3],[0.5,0.3],[0.5,0.6],[0.2,0.6]]`

### Requirement: Polygon utility functions for derived metrics

The system SHALL provide utility functions to compute derived spatial metrics from polygon coordinates.

#### Scenario: Bounding rect from polygon
- **WHEN** a polygon has vertices `[[0.1,0.2],[0.4,0.15],[0.5,0.3],[0.2,0.35]]`
- **THEN** `polygonBounds` returns `{minX: 0.1, minY: 0.15, maxX: 0.5, maxY: 0.35}`

#### Scenario: Center X from polygon
- **WHEN** a polygon has vertices `[[0.1,0.2],[0.3,0.2],[0.3,0.4],[0.1,0.4]]`
- **THEN** `polygonCenterX` returns `0.2`

#### Scenario: Bottom Y from polygon
- **WHEN** a polygon has vertices `[[0.1,0.2],[0.3,0.15],[0.3,0.4],[0.1,0.35]]`
- **THEN** `polygonBottomY` returns `0.4`

#### Scenario: Min X from polygon
- **WHEN** a polygon has vertices `[[0.15,0.2],[0.3,0.2],[0.3,0.4],[0.1,0.4]]`
- **THEN** `polygonMinX` returns `0.1`

### Requirement: Point-in-polygon hit-testing

The system SHALL use a ray casting algorithm to determine if a point is inside an annotation's polygon for click and hover detection.

#### Scenario: Click inside irregular polygon is detected
- **WHEN** the user clicks at normalized coordinates (0.25, 0.3) and an annotation has a polygon that contains that point
- **THEN** the annotation is identified as the click target

#### Scenario: Click outside polygon is not detected
- **WHEN** the user clicks at a point outside all annotation polygons
- **THEN** no annotation is identified as the click target

#### Scenario: Overlapping polygons select topmost
- **WHEN** the user clicks at a point inside two overlapping annotation polygons
- **THEN** the annotation drawn last (topmost) is selected

### Requirement: Canvas renders polygons as filled paths

The system SHALL render each annotation as a filled and stroked polygon path on the canvas, using `beginPath`/`moveTo`/`lineTo`/`closePath`.

#### Scenario: Syllable polygon rendered with correct colors
- **WHEN** the canvas draws a syllable annotation
- **THEN** the polygon is filled with syllable color (blue, semi-transparent) and stroked with syllable border color

#### Scenario: Neume polygon rendered with correct colors
- **WHEN** the canvas draws a neume annotation
- **THEN** the polygon is filled with neume color (red, semi-transparent) and stroked with neume border color

#### Scenario: Selected annotation has highlight border
- **WHEN** a selected annotation is rendered
- **THEN** the polygon stroke uses the selected border color (gold) with increased line width

### Requirement: Preview rectangle rendered as polygon path

The system SHALL render the drag preview as a polygon path (not fillRect/strokeRect) for visual consistency.

#### Scenario: Preview rect rendered during drag
- **WHEN** the user is dragging to draw a new annotation
- **THEN** the preview rectangle is rendered as a dashed polygon path with green fill

### Requirement: Closest point on polygon for curve endpoints

The system SHALL compute the closest point on a polygon's edges to a given external point, for use in neume-to-syllable assignment curve drawing.

#### Scenario: Closest point on polygon edge
- **WHEN** a neume anchor point is at (0.3, 0.1) and the target syllable polygon has an edge from (0.2, 0.4) to (0.4, 0.4)
- **THEN** the closest point is computed on the nearest polygon edge segment

### Requirement: Polygon coordinate conversion between pixels and normalized

The system SHALL provide functions to convert polygon coordinates between pixel space and normalized (0-1) space.

#### Scenario: Normalize pixel polygon
- **WHEN** a polygon `[[100,200],[300,200],[300,400]]` is normalized against a 1000x800 image
- **THEN** the result is `[[0.1,0.25],[0.3,0.25],[0.3,0.5]]`

#### Scenario: Denormalize polygon to pixels
- **WHEN** a polygon `[[0.1,0.25],[0.3,0.25],[0.3,0.5]]` is denormalized against a 1000x800 image
- **THEN** the result is `[[100,200],[300,200],[300,400]]`

### Requirement: Line boundaries stored from OCR results

The system SHALL store text line boundary polygons received from OCR results in app state, associated with the syllable annotation IDs belonging to each line.

#### Scenario: OCR result stores line boundaries
- **WHEN** the backend returns 3 lines, each with a `boundary` polygon and nested syllables
- **THEN** the app state stores 3 line boundary entries, each mapping a boundary polygon to the IDs of the syllable annotations created from that line's syllables

#### Scenario: Line boundaries cleared when annotations are cleared
- **WHEN** the user clears all annotations
- **THEN** stored line boundaries are also cleared

#### Scenario: Line boundaries persist through undo/redo
- **WHEN** the user undoes an OCR operation
- **THEN** the line boundaries from that OCR result are also undone
