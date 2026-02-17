### Requirement: Export contributions to PageXML for segmentation training
The system SHALL provide an `export_segmentation_dataset` function that converts all stored contributions into PageXML files suitable for Kraken segmentation training.

For each contribution, the export SHALL:
1. Load annotations from `contributions/<uuid>/annotations.json`
2. Compute baselines from syllable boundary positions
3. Construct text regions from line boundary polygons
4. Construct neume regions by grouping neume bounding boxes per text line
5. Write a PageXML file to the output directory

#### Scenario: Export contribution with text and neumes
- **WHEN** a contribution exists with line boundaries, syllable boundaries, and neume bounding boxes
- **THEN** export produces a PageXML file containing text regions with baselines and neume regions

#### Scenario: Contribution with no lines
- **WHEN** a contribution has an empty lines array
- **THEN** that contribution is skipped during export

### Requirement: Compute baselines from syllable positions
For each text line, the system SHALL compute a baseline polyline by collecting the bottom-center point of each syllable boundary polygon, sorted by X coordinate.

#### Scenario: Baseline from syllable bottoms
- **WHEN** a line has syllables with boundary polygons at various X positions
- **THEN** the computed baseline is a polyline through the bottom-center of each syllable, ordered left to right

#### Scenario: Line with single syllable
- **WHEN** a line has only one syllable
- **THEN** the baseline is a horizontal segment spanning the syllable's X range at its bottom Y coordinate

#### Scenario: Line with no syllables
- **WHEN** a line has an empty syllables array
- **THEN** that line is skipped (no baseline or text region generated for it)

### Requirement: Construct text regions from line boundaries
Each line boundary polygon from the contribution SHALL become a `text` typed region in the PageXML output. The region contains one `TextLine` element with the computed baseline and the line boundary as its coords.

#### Scenario: Text region with baseline and boundary
- **WHEN** a line has a boundary polygon and syllables for baseline computation
- **THEN** the PageXML contains a `TextRegion` with a `TextLine` whose `Baseline` is the computed polyline and whose `Coords` is the line boundary polygon

### Requirement: Construct neume regions by grouping neumes per text line
For each text line, the system SHALL collect all neume bounding boxes whose vertical center falls above that line (between the previous line's baseline Y and the current line's baseline Y, or the image top for the first line). These neumes SHALL be combined into a single bounding rectangle tagged as region type `neume`.

#### Scenario: Neumes above a text line grouped into one region
- **WHEN** a contribution has 8 neume bboxes positioned above the first text line
- **THEN** the PageXML contains one `neume` region whose boundary is the bounding rectangle of all 8 neume bboxes

#### Scenario: No neumes above a text line
- **WHEN** no neume bounding boxes fall in the vertical band above a text line
- **THEN** no neume region is created for that line

#### Scenario: Neumes between two text lines
- **WHEN** neume bboxes have vertical centers between line 2's baseline Y and line 3's baseline Y
- **THEN** those neumes are grouped into a neume region associated with line 3

### Requirement: PageXML output format
Each exported contribution SHALL produce a valid PageXML file with:
- One `Page` element with image dimensions
- `TextRegion` elements (type `text`) each containing one `TextLine` with `Baseline` and `Coords`
- `ImageRegion` elements (type `neume`) with `Coords` for grouped neume bounding rectangles

#### Scenario: Valid PageXML structure
- **WHEN** export runs for a contribution
- **THEN** the output is a well-formed XML file parseable by Kraken's PageXML reader

### Requirement: Clip overlapping region boundaries at vertical midpoint
After constructing all TextRegion and MusicRegion boundaries, the system SHALL detect vertically overlapping adjacent region pairs and clip their boundaries at the vertical midpoint of the overlap zone. This ensures no pixel belongs to more than one region.

#### Scenario: TextRegion bottom overlaps MusicRegion top
- **WHEN** a TextRegion has Y_max=1178 and the adjacent MusicRegion below has Y_min=1136
- **THEN** the clip line is at Y=1157, the TextRegion boundary is clipped from below at Y=1157, and the MusicRegion boundary is clipped from above at Y=1157

#### Scenario: No overlap between regions
- **WHEN** a TextRegion's Y_max is less than or equal to the adjacent MusicRegion's Y_min
- **THEN** both boundaries are left unchanged

#### Scenario: Polygon clipping preserves shape
- **WHEN** a TextRegion boundary polygon is clipped at a horizontal Y threshold
- **THEN** vertices beyond the threshold are removed, edges crossing the threshold are interpolated to produce new vertices at Y=threshold, and the resulting polygon is closed

#### Scenario: TextLine Coords clipped to match TextRegion
- **WHEN** a TextRegion boundary is clipped
- **THEN** the enclosed TextLine Coords are clipped identically

### Requirement: Dataset output directory structure
The export SHALL write PageXML files and symlink images to a configurable directory (default: `datasets/segmentation/`). The directory SHALL be cleared and recreated on each run.

#### Scenario: Output directory created
- **WHEN** export runs
- **THEN** the output directory contains one `.xml` file and one image file per exported contribution
