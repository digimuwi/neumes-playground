## ADDED Requirements

### Requirement: Line segmentation from image

The system SHALL segment an input image into text lines using Kraken's baseline segmentation model. Each detected line SHALL include its baseline coordinates and bounding polygon.

#### Scenario: Successful line segmentation

- **WHEN** an image of a manuscript page is provided
- **THEN** the system returns a list of detected text lines with baseline and boundary coordinates

#### Scenario: No lines detected

- **WHEN** an image with no text content is provided
- **THEN** the system returns an empty list of lines

### Requirement: Character recognition with geometry

The system SHALL recognize text in each detected line using the Kraken OCR model and TRIDIS weights. For each recognized character, the system SHALL provide the character's position via "cuts" (vertical dividing lines between characters).

#### Scenario: Successful character recognition

- **WHEN** a segmented text line is processed
- **THEN** the system returns the recognized text string, a list of cuts (one per character), and confidence scores per character

#### Scenario: Low confidence recognition

- **WHEN** a character cannot be recognized with high confidence
- **THEN** the system still returns the best-guess character with its confidence score (no filtering)

### Requirement: Character bounding box extraction

The system SHALL compute a bounding box for each recognized character by using consecutive cuts. The left edge is the current character's cut x-position, and the right edge is the next character's cut x-position.

#### Scenario: Extract character bbox

- **WHEN** cuts are available for a line with text "abc"
- **THEN** character 'a' has bbox from cut[0].x to cut[1].x, character 'b' from cut[1].x to cut[2].x, etc.

#### Scenario: Last character bbox

- **WHEN** extracting bbox for the last character
- **THEN** the system estimates the right edge (e.g., cut.x + average_char_width) since there is no next cut

### Requirement: Region-based processing

The system SHALL accept an optional region (x, y, width, height in pixels) to crop the input image before processing. If no region is specified, the entire image is processed.

#### Scenario: Process specific region

- **WHEN** an image and region {x: 100, y: 200, width: 500, height: 150} are provided
- **THEN** only the specified region is segmented and recognized

#### Scenario: Process full image

- **WHEN** an image is provided without a region parameter
- **THEN** the entire image is processed
