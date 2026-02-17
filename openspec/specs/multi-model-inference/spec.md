### Requirement: Custom segmentation model detection
The system SHALL check for custom segmentation model at `models/segmentation.mlmodel`.

#### Scenario: Custom model exists
- **WHEN** `models/segmentation.mlmodel` exists
- **THEN** use custom model for segmentation

#### Scenario: Custom model missing
- **WHEN** `models/segmentation.mlmodel` does not exist
- **THEN** use default Kraken segmentation model

### Requirement: Custom segmentation produces typed lines
When using a custom segmentation model trained on typed data, the system SHALL preserve line type tags.

#### Scenario: Lines have type tags
- **WHEN** custom segmentation model is used
- **THEN** segmentation output lines have `tags` dict with type information
- **THEN** type values are "neume" or "text"

### Requirement: Recognition model detection
The system SHALL detect available recognition models at startup and after training.

#### Scenario: Check for text recognition model
- **WHEN** recognition is requested
- **THEN** check for `models/recognition_text.mlmodel` (custom) or fall back to Tridis model

#### Scenario: Check for neume recognition model
- **WHEN** recognition is requested
- **THEN** check for `models/recognition_neume.mlmodel`

### Requirement: Multi-model routing
When both text and neume recognition models are available, the system SHALL use mm_rpred for routing.

#### Scenario: Both models available
- **WHEN** both `recognition_text.mlmodel` and `recognition_neume.mlmodel` exist
- **THEN** use `mm_rpred` with tag-to-model mapping
- **THEN** lines tagged "type:text" are processed by text model
- **THEN** lines tagged "type:neume" are processed by neume model

### Requirement: Single model fallback
When only the text recognition model is available, the system SHALL use single-model recognition.

#### Scenario: Only text model available
- **WHEN** text recognition model exists AND neume model does not exist
- **THEN** use `rpred` with text model only
- **THEN** lines tagged as neume type are skipped

### Requirement: Graceful handling of untyped lines
When using default segmentation (no type tags), the system SHALL process all lines with the text model.

#### Scenario: Default segmentation with single model
- **WHEN** default segmentation is used (no line type tags)
- **THEN** all lines are processed with text recognition model
- **THEN** behavior matches current system

### Requirement: Model caching
Loaded models SHALL be cached to avoid reloading on each request.

#### Scenario: Models cached in memory
- **WHEN** a model is loaded
- **THEN** it is cached for subsequent requests
- **WHEN** model file is updated (newer mtime)
- **THEN** model is reloaded on next request
