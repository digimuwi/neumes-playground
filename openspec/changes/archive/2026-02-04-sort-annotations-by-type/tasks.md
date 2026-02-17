## 1. Implementation

- [x] 1.1 Add `TYPE_PRIORITY` constant array defining sort order: `['syllable', 'neume']`
- [x] 1.2 Rename `sortAnnotationsByReadingOrder` to `sortAnnotationsForCycling`
- [x] 1.3 Modify sort function to compare by type priority first, then by reading order

## 2. Verification

- [x] 2.1 Test Tab cycles through all syllables before any neumes
- [x] 2.2 Test Shift+Tab cycles backwards (neumes first, then syllables)
- [x] 2.3 Test reading order is preserved within each type group
