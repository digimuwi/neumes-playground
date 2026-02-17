### Requirement: Update contribution annotations via PUT endpoint

The system SHALL provide a `PUT /contributions/{id}` endpoint that accepts a `ContributionAnnotations` JSON body and replaces the `lines` and `neumes` in the stored `annotations.json`.

The `image` metadata block in `annotations.json` SHALL be preserved from the existing file — the PUT request does not include or modify image metadata.

The endpoint SHALL return a `ContributionResponse` with the contribution ID and a success message on successful update.

#### Scenario: Successful annotation update
- **WHEN** client sends PUT to `/contributions/{id}` with valid `ContributionAnnotations` JSON body
- **THEN** system returns HTTP 200 with `{"id": "<uuid>", "message": "Contribution updated successfully"}`
- **AND** the stored `annotations.json` contains the new `lines` and `neumes`
- **AND** the stored `annotations.json` preserves the original `image` metadata block

#### Scenario: Update preserves image metadata
- **WHEN** client sends PUT to `/contributions/{id}` with new annotations
- **THEN** the `image` field in `annotations.json` remains unchanged (same filename, width, height)

#### Scenario: Contribution not found for update
- **WHEN** client sends PUT to `/contributions/{id}` with a non-existent contribution ID
- **THEN** system returns HTTP 404 with an error detail message

#### Scenario: Invalid annotations for update
- **WHEN** client sends PUT to `/contributions/{id}` with invalid JSON or malformed annotations
- **THEN** system returns HTTP 422 with a validation error

#### Scenario: Invalid contribution ID for update
- **WHEN** client sends PUT to `/contributions/{id}` with a non-UUID string
- **THEN** system returns HTTP 404 with an error detail message
