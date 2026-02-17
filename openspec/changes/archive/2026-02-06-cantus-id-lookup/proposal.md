## Why

The Cantus Index database was originally used for text suggestions during syllable annotation, but OCR has proven reliable enough that this feature is no longer needed. However, the Cantus Index remains valuable for attaching Cantus IDs to annotated chants, enabling scholarly cross-referencing and metadata enrichment.

## What Changes

- Add on-demand Cantus ID lookup that queries the Cantus Index API using the annotated syllable text
- Store Cantus metadata (cid, genre) at document level in AppState
- Show selection dialog when multiple chants match the query
- Display "No matching chant found" message when no results
- Include Cantus ID and genre in MEI export when present

## Capabilities

### New Capabilities

- `cantus-id-lookup`: On-demand lookup of Cantus ID from annotated text, with selection dialog for multiple matches and document-level metadata storage

### Modified Capabilities

- `mei-export`: Include Cantus metadata (cid, genre) in `<meiHead>` section when present

## Impact

- **State**: Add `metadata` field to `AppState` for document-level metadata (extensible for future fields)
- **Actions**: Add `SET_METADATA` action type
- **Services**: Reuse existing `fetchChants()` from `cantusIndex.ts`
- **UI**: New "Find Cantus ID" button (location TBD) and selection dialog component
- **Export**: MEI export includes `<workList>` with Cantus identifier when metadata is present
