## ADDED Requirements

### Requirement: List all stored contributions

The contribution storage module SHALL provide a function to list all stored contribution directories.

The function SHALL return a list of `(contribution_id, contribution_path)` tuples for all valid contributions (directories containing both an image file and `annotations.json`).

Directories that are missing either file SHALL be skipped with a warning logged.

#### Scenario: List contributions from populated directory
- **WHEN** `contributions/` contains three valid contribution directories
- **THEN** the list function returns three entries with their UUIDs and paths

#### Scenario: List contributions from empty directory
- **WHEN** `contributions/` exists but contains no subdirectories
- **THEN** the list function returns an empty list

#### Scenario: Skip malformed contribution
- **WHEN** a subdirectory under `contributions/` is missing `annotations.json`
- **THEN** the list function skips it, logs a warning, and returns only valid contributions
