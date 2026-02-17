### Requirement: List all contributions via GET endpoint

The system SHALL provide a `GET /contributions` endpoint that returns a JSON array of `ContributionSummary` objects for all valid stored contributions.

Each `ContributionSummary` SHALL contain:
- `id` (string): the contribution UUID
- `image` (object): `{ filename, width, height }` from the stored `annotations.json`
- `line_count` (int): number of lines in the contribution
- `syllable_count` (int): total number of syllables across all lines
- `neume_count` (int): number of neumes in the contribution

The endpoint SHALL return an empty array if no contributions exist.

Invalid contribution directories (missing image or annotations.json) SHALL be skipped.

#### Scenario: List contributions from populated directory
- **WHEN** client sends GET to `/contributions` and three valid contributions exist
- **THEN** system returns HTTP 200 with a JSON array of three `ContributionSummary` objects
- **AND** each summary contains the contribution ID, image metadata, and annotation counts

#### Scenario: List contributions when empty
- **WHEN** client sends GET to `/contributions` and no contributions exist
- **THEN** system returns HTTP 200 with an empty JSON array `[]`

#### Scenario: Malformed contributions are skipped
- **WHEN** client sends GET to `/contributions` and some contribution directories are missing required files
- **THEN** system returns only the valid contributions and skips malformed ones

### Requirement: Retrieve a single contribution via GET endpoint

The system SHALL provide a `GET /contributions/{id}` endpoint that returns the full contribution data including the base64-encoded image.

The response SHALL contain:
- `id` (string): the contribution UUID
- `image` (object): `{ filename, width, height, data_url }` where `data_url` is a base64-encoded data URL (e.g., `data:image/jpeg;base64,...`)
- `lines` (array): the line annotations from `annotations.json`
- `neumes` (array): the neume annotations from `annotations.json`

#### Scenario: Retrieve existing contribution
- **WHEN** client sends GET to `/contributions/{id}` with a valid contribution ID
- **THEN** system returns HTTP 200 with the full contribution data
- **AND** the `image.data_url` field contains the base64-encoded image as a data URL
- **AND** the `lines` and `neumes` arrays match the stored `annotations.json`

#### Scenario: Contribution not found
- **WHEN** client sends GET to `/contributions/{id}` with a non-existent contribution ID
- **THEN** system returns HTTP 404 with an error detail message

#### Scenario: Invalid contribution ID format
- **WHEN** client sends GET to `/contributions/{id}` with a non-UUID string (e.g., `../etc/passwd`)
- **THEN** system returns HTTP 404 with an error detail message

### Requirement: Contribution ID validation

The system SHALL validate that contribution ID path parameters conform to UUID format before accessing the filesystem.

Non-UUID strings SHALL be rejected with HTTP 404 to prevent path traversal attacks.

#### Scenario: Valid UUID accepted
- **WHEN** a request uses a valid UUID string as the contribution ID
- **THEN** system proceeds to look up the contribution in the filesystem

#### Scenario: Path traversal attempt rejected
- **WHEN** a request uses `../../etc/passwd` as the contribution ID
- **THEN** system returns HTTP 404 without accessing any filesystem path outside the contributions directory
