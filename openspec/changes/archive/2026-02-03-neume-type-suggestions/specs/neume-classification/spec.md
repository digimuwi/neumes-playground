## ADDED Requirements

### Requirement: Binary image representation
The classifier SHALL accept binary images as a `BinaryImage` type containing:
- `data`: `Uint8Array` where 1 = foreground (ink), 0 = background
- `width`: image width in pixels
- `height`: image height in pixels

#### Scenario: Valid binary image input
- **WHEN** classifier receives a BinaryImage with correct dimensions
- **THEN** classifier processes the image and returns results

### Requirement: Zhang-Suen skeletonization
The classifier SHALL reduce binary images to 1-pixel-wide skeletons using the Zhang-Suen thinning algorithm, preserving:
- Neighbor ordering P2-P9 in clockwise order starting from top
- Two sub-iterations per pass with distinct deletion conditions
- Iteration until no pixels change in either sub-iteration

#### Scenario: Skeleton preserves topology
- **WHEN** a binary image of a stroke is skeletonized
- **THEN** the skeleton maintains connectivity of the original stroke

#### Scenario: Skeleton is 1-pixel wide
- **WHEN** skeletonization completes
- **THEN** no foreground pixel has more than 2 orthogonal foreground neighbors

### Requirement: Graph extraction from skeleton
The classifier SHALL convert skeletons to graphs where:
- Each foreground pixel becomes a node with (row, col) coordinates
- Edges connect 8-adjacent foreground pixels
- Adjacency is stored as a list of neighbor indices per node

#### Scenario: Graph represents skeleton connectivity
- **WHEN** skeleton is converted to graph
- **THEN** connected skeleton regions become connected graph components

### Requirement: Connected component detection
The classifier SHALL identify connected components in the skeleton graph using depth-first or breadth-first traversal.

#### Scenario: Separate strokes become separate components
- **WHEN** skeleton has two disconnected regions
- **THEN** classifier identifies two distinct connected components

### Requirement: Gap closing for broken strokes
The classifier SHALL attempt to close gaps between skeleton endpoints that are:
- Within 70 pixels distance
- In different connected components
- Directionally consistent (angle < 20° between endpoint direction and gap direction)

Endpoint direction is estimated by walking up to 6 steps along the skeleton from the endpoint.

#### Scenario: Small aligned gap is closed
- **WHEN** two endpoints are 50 pixels apart and directionally aligned
- **THEN** classifier draws a line connecting them on the skeleton

#### Scenario: Large gap is not closed
- **WHEN** two endpoints are 100 pixels apart
- **THEN** classifier does NOT connect them

#### Scenario: Misaligned gap is not closed
- **WHEN** two endpoints are close but at 45° angle to their stroke directions
- **THEN** classifier does NOT connect them

### Requirement: Border component filtering
The classifier SHALL ignore skeleton components that touch the image border AND have approximate length less than 50 pixels, as these are likely artifacts from neighboring neumes.

#### Scenario: Small border artifact filtered
- **WHEN** a 30-pixel component touches the image edge
- **THEN** that component is excluded from analysis

#### Scenario: Large border-touching stroke kept
- **WHEN** a 100-pixel component touches the image edge
- **THEN** that component is included in analysis

### Requirement: Main stroke extraction
The classifier SHALL extract the main stroke from each component by finding the longest shortest-path between any two endpoints (degree-1 nodes), effectively removing branches.

#### Scenario: Branches removed from stroke
- **WHEN** a stroke has a small branch
- **THEN** only the main path is kept for analysis

### Requirement: Dot detection
The classifier SHALL classify strokes with skeleton path length less than 40 pixels as dots, represented by token `"0"`.

#### Scenario: Small stroke becomes dot
- **WHEN** stroke path length is 30 pixels
- **THEN** stroke is classified as dot token `"0"`

#### Scenario: Normal stroke is not a dot
- **WHEN** stroke path length is 60 pixels
- **THEN** stroke proceeds to movement analysis

### Requirement: RDP polyline simplification
The classifier SHALL simplify stroke paths using the Ramer-Douglas-Peucker algorithm with epsilon tolerance of 2.0 pixels.

#### Scenario: Noisy path is smoothed
- **WHEN** a jagged path is simplified
- **THEN** result has fewer points while preserving overall shape

### Requirement: Vertical movement sequence
The classifier SHALL analyze simplified strokes left-to-right, sampling points at regular arc-length intervals, and classifying each segment as:
- `"u"` (up) if y decreases by more than 3 pixels
- `"d"` (down) if y increases by more than 3 pixels
- `"s"` (straight) if y change is within 3 pixels

Note: In image coordinates, y increases downward.

#### Scenario: Ascending stroke
- **WHEN** stroke goes from bottom-left to top-right
- **THEN** movement sequence contains `"u"` tokens

#### Scenario: Descending stroke
- **WHEN** stroke goes from top-left to bottom-right
- **THEN** movement sequence contains `"d"` tokens

### Requirement: Run-length tokenization
The classifier SHALL convert movement sequences to run-length tokens by:
1. Grouping consecutive same-direction movements into runs
2. Normalizing run lengths as fractions of total
3. Bucketing: <0.25 = "S" (short), <0.5 = "M" (medium), ≥0.5 = "L" (long)
4. Combining direction and bucket: e.g., `"uL"`, `"dS"`
5. Filtering out straight (`"s"`) segments

#### Scenario: Movement sequence tokenized
- **WHEN** movements are `["d", "d", "u", "u", "u", "u"]`
- **THEN** runs are `[("d", 2), ("u", 4)]`, normalized to `[("d", 0.33), ("u", 0.67)]`, tokens are `["dM", "uL"]`

### Requirement: Stroke ordering
The classifier SHALL order strokes left-to-right by their minimum x-coordinate before combining tokens.

#### Scenario: Multiple strokes ordered
- **WHEN** image has a dot on the right and a stroke on the left
- **THEN** stroke tokens come before dot token

### Requirement: Needleman-Wunsch alignment scoring
The classifier SHALL match token sequences against lexicon patterns using Needleman-Wunsch global alignment with scoring:
- Same direction, same magnitude: +3
- Same direction, different magnitude: +1
- Straight vs up/down: -1
- Opposite directions (u vs d): -3
- Dot match: +2
- Dot mismatch: -1
- Gap penalty: -2

#### Scenario: Perfect match scores highest
- **WHEN** token sequence exactly matches a lexicon pattern
- **THEN** that pattern has the highest alignment score

#### Scenario: Similar patterns score well
- **WHEN** token sequence differs by one magnitude (e.g., `"uL"` vs `"uM"`)
- **THEN** alignment score is positive but lower than exact match

### Requirement: Lexicon matching
The classifier SHALL match token sequences against a built-in lexicon of neume types and return the top 5 matches ranked by alignment score.

#### Scenario: Pes classification
- **WHEN** tokens are `["dS", "uL"]` (down-short, up-long)
- **THEN** "pes" ranks among top suggestions

#### Scenario: Punctum classification
- **WHEN** tokens are `["0"]` (single dot)
- **THEN** "punctum" ranks as top suggestion

### Requirement: Return ranked suggestions
The classifier SHALL return an array of suggestions, each with `name` (neume type) and `score` (alignment score), sorted by score descending, limited to top 5.

#### Scenario: Multiple suggestions returned
- **WHEN** classification completes
- **THEN** result contains up to 5 suggestions with name and score

### Requirement: Handle empty images
The classifier SHALL return an empty suggestions array when the image contains no foreground pixels or no classifiable strokes.

#### Scenario: Empty image
- **WHEN** binary image has no foreground pixels
- **THEN** classifier returns empty suggestions array
