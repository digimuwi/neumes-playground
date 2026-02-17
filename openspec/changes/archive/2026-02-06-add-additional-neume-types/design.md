## Context

The application has a `NeumeType` enum in `src/state/types.ts` and a corresponding `neumeTypes` array in `src/data/neumeTypes.ts`. This follows the same pattern established in the recent episema change. Adding new neume types is straightforward: add enum values and metadata entries.

## Goals / Non-Goals

**Goals:**
- Add 7 new neume types: cephalicus, equaliter, inferius, levare, mediocriter, pressionem, sursum
- Follow existing naming conventions (lowercase enum values, capitalized display names)

**Non-Goals:**
- Automatic classification (these are specialized types not suitable for visual detection)
- Grouping or categorization in the UI (all types remain in a single flat list)

## Decisions

### 1. Enum naming convention

**Decision**: Use single lowercase words matching the Latin terms (e.g., `CEPHALICUS = 'cephalicus'`)

**Rationale**: Consistent with existing types like `punctum`, `quilisma`, `salicus`.

### 2. Descriptions for each type

**Decision**: Use brief musicological descriptions:
- Cephalicus: "Liquescent descending neume"
- Equaliter: "Equal rhythmic value indication"
- Inferius: "Lower pitch indication"
- Levare: "Upward melodic movement"
- Mediocriter: "Moderate rhythmic value"
- Pressionem: "Pressure/emphasis marking"
- Sursum: "Upward direction indicator"

**Rationale**: Descriptions help users identify the correct neume type when annotating.

## Risks / Trade-offs

**[Trade-off]** Dropdown continues to grow → Acceptable; users can type to filter.
