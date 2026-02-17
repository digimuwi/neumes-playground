## Why

MEI exports currently lack word boundary information. When users enter syllables with trailing hyphens (e.g., "Al-", "le-", "lu-", "ia") to indicate multi-syllable words, this information is lost on export. The MEI standard provides a `@wordpos` attribute on `<syl>` elements to encode word position, which is essential for proper rendering and text reconstruction.

## What Changes

- Compute `wordpos` attribute ("i", "m", "t", "s") from hyphen convention during MEI export
- Strip trailing hyphens from syllable text in `<syl>` output
- Empty syllables skip wordpos computation but don't break word chains

## Capabilities

### New Capabilities

None - this extends existing MEI export functionality.

### Modified Capabilities

- `mei-export`: Add wordpos attribute computation based on hyphen convention in syllable text

## Impact

- `src/utils/meiExport.ts`: Add wordpos computation logic and modify `generateSyllableXML()` to emit the attribute
