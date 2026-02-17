## Why

The syllable boxes displayed to users show individual syllables without visual indication of word continuity. Users cannot easily tell if "Be" "ne" "dic" "tus" is one word or four. Adding trailing hyphens to non-final syllables ("Be-" "ne-" "dic-" "tus") provides clear visual feedback about word structure.

## What Changes

- Modify syllable text output to include trailing hyphens for syllables that continue within a word
- Final syllables of each word remain unhyphenated
- Single-syllable words remain unhyphenated

## Capabilities

### New Capabilities

- `syllable-formatting`: Rules for how syllable text is formatted when returned to clients, including hyphenation for word continuity

### Modified Capabilities

None - this is a new behavioral specification, not a modification to existing specs.

## Impact

- **Code**: `src/htr_service/syllabification/latin.py` - the `syllabify_word()` function
- **API**: The `text` field in syllable responses will now include trailing hyphens for non-final syllables
- **Clients**: Frontend syllable boxes will display hyphens - no client changes needed, this is the desired behavior
