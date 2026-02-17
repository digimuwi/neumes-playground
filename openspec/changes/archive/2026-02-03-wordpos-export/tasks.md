## 1. Wordpos Computation

- [x] 1.1 Add `computeWordpos()` function that takes syllables in reading order and returns a Map<syllableId, wordpos>
- [x] 1.2 Add `stripHyphen()` helper function to remove trailing hyphen from text

## 2. Export Integration

- [x] 2.1 Modify `generateSyllableXML()` to accept wordpos parameter and emit the attribute on `<syl>`
- [x] 2.2 Update `generateMEI()` to compute wordpos map and pass values to `generateSyllableXML()`
