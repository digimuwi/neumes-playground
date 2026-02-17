## Context

The application has a `NeumeType` enum in `src/state/types.ts` with 24 neume types, and a corresponding `neumeTypes` array in `src/data/neumeTypes.ts` that provides display metadata. Users select neume types from a Material-UI Autocomplete dropdown in the `InlineAnnotationEditor` component.

The apostropha neume type is currently missing, and there's no way to indicate episema (a horizontal stroke indicating prolongation) on any neume.

## Goals / Non-Goals

**Goals:**
- Add apostropha as a base neume type
- Add episema variants for virga, clivis, climacus, and apostropha
- Maintain consistency with existing naming convention (space-separated, e.g., "pes subbipunctis")

**Non-Goals:**
- Automatic classification of episema (visually indistinguishable for the classifier)
- Separate episema property on the Annotation interface (using enum variants keeps data model simple)
- Backend changes (existing API accepts any string for neume type)

## Decisions

### 1. Episema as separate enum values vs. boolean property

**Decision**: Add episema variants as separate enum values (e.g., `VIRGA_EPISEMA = 'virga episema'`)

**Alternatives considered**:
- Boolean `episema` property on Annotation: Would require schema changes, action updates, UI changes for conditional checkbox. More flexible but higher complexity.
- Suffix in display name only: Would lose the distinction in exports and data.

**Rationale**: Separate enum values match the existing pattern for compound neumes (e.g., `pes subbipunctis`), require minimal code changes, and export cleanly to MEI.

### 2. Naming convention

**Decision**: Use space-separated lowercase (e.g., `'virga episema'`) matching existing compound types.

**Rationale**: Consistent with `'pes subbipunctis'`, `'scandicus flexus'`, etc.

### 3. Display name format

**Decision**: Capitalize first letter only (e.g., "Virga episema", "Clivis episema")

**Rationale**: Matches existing pattern like "Pes subbipunctis", "Scandicus flexus".

## Risks / Trade-offs

**[Risk]** Dropdown gets longer with more options → Users can type to filter, so impact is minimal.

**[Trade-off]** Episema variants can't be auto-suggested by classifier → Acceptable; users manually select episema when needed.

**[Trade-off]** Data model treats base and episema as unrelated types → Simple, but can't easily query "all virga variants". Acceptable for current use case.
