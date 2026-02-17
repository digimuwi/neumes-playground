## 1. Syllable Text Processing

- [x] 1.1 Add helper function to strip trailing hyphens from syllable text
- [x] 1.2 Apply hyphen stripping when building Word elements for syllables
- [x] 1.3 Update line-level TextEquiv to use stripped syllable text

## 2. Neume Band Grouping

- [x] 2.1 Add function to group neumes by vertical overlap into bands
- [x] 2.2 Sort neumes within each band left-to-right by x-coordinate
- [x] 2.3 Compute bounding box and baseline for each neume band

## 3. TextLine Structure Changes

- [x] 3.1 Add `custom` attribute with `structure {type:text;}` to text TextLines
- [x] 3.2 Refactor neume generation to create TextLines with Word children instead of individual TextLines
- [x] 3.3 Add `custom` attribute with `structure {type:neume;}` to neume TextLines

## 4. Region Consolidation

- [x] 4.1 Replace separate text/neume TextRegions with single content TextRegion
- [x] 4.2 Compute combined bounding box for all content
- [x] 4.3 Interleave text and neume TextLines in reading order (by y-coordinate)

## 5. Testing

- [x] 5.1 Update existing PAGE XML generation tests for new structure
- [x] 5.2 Add test for syllable hyphen stripping
- [x] 5.3 Add test for neume band grouping logic
- [x] 5.4 Add test for custom type attributes on TextLines
- [x] 5.5 Add test for single content region with mixed content
