## Why

Users need to annotate neumes that have an episema (a horizontal stroke indicating prolongation or emphasis). Currently, virga, clivis, climacus can be annotated, but there's no way to mark them as having an episema. Additionally, the apostropha neume type is missing entirely.

## What Changes

- Add 5 new neume type enum values: `apostropha`, `virga episema`, `clivis episema`, `climacus episema`, `apostropha episema`
- Add corresponding entries to the neume types configuration array with display names and descriptions
- These will appear in the neume type dropdown alongside existing types

## Capabilities

### New Capabilities

- `episema-neume-types`: Adds episema variants for virga, clivis, climacus, and apostropha, plus the base apostropha type

### Modified Capabilities

<!-- No existing spec requirements are changing -->

## Impact

- `src/state/types.ts`: New enum values in `NeumeType`
- `src/data/neumeTypes.ts`: New entries in the `neumeTypes` array
- MEI export will use the new type strings as-is (e.g., `type="virga episema"`)
- No changes to classifier (episema not visually distinguishable for auto-detection)
- No impact on undo/redo or coordinate system
