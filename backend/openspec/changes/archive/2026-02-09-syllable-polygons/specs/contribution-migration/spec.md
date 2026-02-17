## ADDED Requirements

### Requirement: Migrate existing contributions to polygon-based format

The system SHALL provide a one-time migration script (invocable as `python -m htr_service.scripts.migrate_contributions`) that converts existing `annotations.json` files from bbox-based syllables to polygon-based syllables.

For each contribution, the script SHALL:
1. Load the image and run Kraken segmentation to obtain line boundary polygons
2. Run Kraken OCR to obtain character cuts per line
3. Match existing syllable annotations to OCR results by spatial overlap and text content
4. Slice matched line polygons into per-syllable polygons using character cuts
5. Rewrite `annotations.json` in the new format with polygon boundaries

#### Scenario: Migrate a contribution with matching syllables
- **WHEN** the script processes a contribution whose stored syllables match the OCR results
- **THEN** `annotations.json` is rewritten with syllable `boundary` polygons derived from the segmentation

#### Scenario: Migrate a contribution where user removed syllables
- **WHEN** the script processes a contribution where the user had removed some syllable boxes (fewer stored syllables than OCR produces)
- **THEN** only the syllables present in the existing annotations get polygon boundaries
- **AND** Kraken lines with no matching stored syllables are discarded

### Requirement: Match stored syllables to OCR results

The migration script SHALL match stored syllables to OCR-produced syllables using spatial overlap as the primary signal. For each Kraken line, the script SHALL find stored syllables whose bounding boxes overlap the line's boundary polygon, then match individual syllables by text content and x-position within that line.

#### Scenario: Syllable matched by overlap and text
- **WHEN** a stored syllable with text "mi-" and bbox overlapping a Kraken line exists, and the OCR result for that line also contains "mi-"
- **THEN** the stored syllable is matched and receives its polygon boundary from the sliced line polygon

#### Scenario: Unmatched OCR syllable
- **WHEN** the OCR produces a syllable that has no corresponding stored syllable (user had removed it)
- **THEN** that OCR syllable is not included in the migrated annotations

#### Scenario: Unmatched stored syllable
- **WHEN** a stored syllable cannot be matched to any OCR result (e.g., OCR produces different text)
- **THEN** the script logs a warning and keeps the syllable with a rectangular polygon derived from its existing bbox as a fallback

### Requirement: Preserve neume annotations during migration

The migration script SHALL preserve all neume annotations exactly as they are. Only the `lines` structure changes.

#### Scenario: Neumes unchanged after migration
- **WHEN** the script processes a contribution with neume annotations
- **THEN** the neume entries in the migrated `annotations.json` are identical to the original

### Requirement: Create backup before migration

The migration script SHALL create a backup of each `annotations.json` as `annotations.json.bak` before overwriting.

#### Scenario: Backup created
- **WHEN** the script migrates a contribution
- **THEN** `annotations.json.bak` exists with the original file contents

### Requirement: Idempotent migration

The migration script SHALL detect contributions already in the new format (syllables with `boundary` fields) and skip them.

#### Scenario: Already-migrated contribution
- **WHEN** the script encounters a contribution whose syllables already have `boundary` fields
- **THEN** it skips that contribution and logs that it is already migrated

### Requirement: Print migration summary

The script SHALL print a summary of how many contributions were migrated, skipped, and any that had warnings.

#### Scenario: Migration summary output
- **WHEN** the script finishes processing all contributions
- **THEN** it prints counts of migrated, skipped (already new format), and contributions with unmatched syllables
