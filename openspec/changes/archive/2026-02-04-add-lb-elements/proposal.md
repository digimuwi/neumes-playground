## Why

The MEI export currently outputs syllables in reading order but loses explicit line-break information. Adding `<lb/>` (line beginning) elements preserves the visual layout of the manuscript, enabling downstream tools to reconstruct line structure for display or analysis.

## What Changes

- Insert `<lb n="N"/>` elements in the MEI export to mark the beginning of each text line
- Line numbers start at 1 and increment for each non-empty text line
- `<lb/>` appears before the first syllable of each line (including line 1)
- Empty lines (with no syllables) do not generate `<lb/>` elements

## Capabilities

### New Capabilities

None - this extends existing MEI export functionality.

### Modified Capabilities

- `mei-export`: Add line beginning markers to preserve manuscript layout structure

## Impact

- `src/utils/meiExport.ts`: Modify `generateMEI()` to emit `<lb/>` elements between text lines
- Existing MEI export tests will need updates to account for new `<lb/>` elements in output
