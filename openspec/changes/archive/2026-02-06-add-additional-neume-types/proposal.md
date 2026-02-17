## Why

Users need to annotate additional neume types that are currently missing from the application: cephalicus, equaliter, inferius, levare, mediocriter, pressionem, and sursum. These are performance indications and ornamental neume forms found in medieval manuscripts.

## What Changes

- Add 7 new neume type enum values: `cephalicus`, `equaliter`, `inferius`, `levare`, `mediocriter`, `pressionem`, `sursum`
- Add corresponding entries to the neume types configuration array with display names and descriptions
- These will appear in the neume type dropdown alongside existing types

## Capabilities

### New Capabilities

- `additional-neume-types`: Adds cephalicus, equaliter, inferius, levare, mediocriter, pressionem, and sursum neume types

### Modified Capabilities

<!-- No existing spec requirements are changing -->

## Impact

- `src/state/types.ts`: New enum values in `NeumeType`
- `src/data/neumeTypes.ts`: New entries in the `neumeTypes` array
- MEI export will use the new type strings as-is
- No changes to classifier
- No impact on undo/redo or coordinate system
