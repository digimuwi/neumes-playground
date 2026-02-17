## Context

The MEI export (`src/utils/meiExport.ts`) already computes text lines via `computeTextLines()` and iterates through them in `getSyllablesInReadingOrder()`. However, the line structure is flattened when generating syllable elements - no `<lb/>` markers are emitted.

The `<lb/>` element in MEI marks "line beginning" and is used to preserve manuscript layout information in the encoded output.

## Goals / Non-Goals

**Goals:**
- Emit `<lb n="N"/>` elements to mark the start of each text line in MEI export
- Preserve existing syllable ordering and neume assignment behavior
- Maintain valid MEI output structure

**Non-Goals:**
- Adding facsimile zones for line regions (only `n` attribute, no `facs`)
- Changing text line detection logic
- Supporting `<pb/>` (page break) elements

## Decisions

### Decision 1: Emit `<lb/>` before line content, including first line

**Choice**: Insert `<lb n="N"/>` before the first syllable of each line, starting with `<lb n="1"/>` before line 1.

**Rationale**: The `<lb/>` element semantically means "line beginning", so it belongs at the start of each line. Including it for line 1 provides consistent structure and makes line counting unambiguous.

**Alternative considered**: Only emit `<lb/>` between lines (starting at line 2). Rejected because it's inconsistent - line 1 would be the only line without an explicit marker.

### Decision 2: Skip empty lines

**Choice**: Only emit `<lb/>` for lines that contain at least one syllable.

**Rationale**: Empty detected lines (edge case from line detection) have no content to mark. Emitting `<lb/>` without following content would be misleading.

### Decision 3: Refactor `generateMEI()` to iterate by line

**Choice**: Replace the current pattern of flattening syllables with direct iteration over `textLines`.

**Rationale**: The current flow is:
```
textLines → getSyllablesInReadingOrder() → flat list → map to XML
```

The new flow will be:
```
textLines → for each line: emit <lb/>, then syllables in that line
```

This preserves line boundaries naturally. The `wordposMap` computation remains unchanged since it still needs the flat reading-order list.

## Risks / Trade-offs

**Risk**: Tests that assert exact MEI output will fail.
→ Mitigation: Update test expectations to include `<lb/>` elements.

**Risk**: Downstream tools may not expect `<lb/>` elements.
→ Mitigation: `<lb/>` is standard MEI - compliant tools should handle it. Non-compliant tools would need updates regardless.
