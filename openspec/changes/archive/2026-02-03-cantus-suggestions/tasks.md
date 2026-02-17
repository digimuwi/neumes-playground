## 1. Dependencies

- [x] 1.1 Install `hyphen` package: `npm install hyphen`

## 2. Text Reconstruction

- [x] 2.1 Create `src/utils/textReconstruction.ts` with `reconstructQueryText(annotations: Annotation[], newAnnotation: Annotation): string`
- [x] 2.2 Implement reading order logic: use `computeTextLines` including new annotation, slice syllables before it
- [x] 2.3 Implement word reconstruction: strip hyphens, concatenate syllables, exclude incomplete final word

## 3. Cantus Index Service

- [x] 3.1 Create `src/services/cantusIndex.ts` with types for API response (`CantusChant: { cid, fulltext, genre }`)
- [x] 3.2 Implement in-memory cache (Map keyed by query string)
- [x] 3.3 Implement `fetchChants(query: string): Promise<CantusChant[]>` with cache check
- [x] 3.4 Implement progressive shortening: retry with first word removed on zero results

## 4. Next Word Extraction

- [x] 4.1 Implement `extractNextWord(chants: CantusChant[], query: string): string | null`
- [x] 4.2 Find word after query string in each chant fulltext
- [x] 4.3 Count occurrences and return most common (first on tie)

## 5. Latin Syllabification

- [x] 5.1 Create syllabification utility using `hyphen/la-x-liturgic`
- [x] 5.2 Implement `syllabifyWord(word: string): Promise<string[]>`
- [x] 5.3 Implement `formatSuggestion(syllables: string[]): string` (add hyphen if not last syllable)

## 6. Suggestion Hook

- [x] 6.1 Create `src/hooks/useSuggestion.ts`
- [x] 6.2 Implement `useSuggestion(annotations: Annotation[], currentAnnotation: Annotation | null, isNewlyCreated: boolean): string | null`
- [x] 6.3 Orchestrate: reconstruct text → fetch chants → extract next word → syllabify → format
- [x] 6.4 Handle errors gracefully (return null on any failure)

## 7. UI Integration

- [x] 7.1 Add ghost text styling to syllable TextField in `InlineAnnotationEditor`
- [x] 7.2 Pass suggestion from `useSuggestion` hook to the editor
- [x] 7.3 Implement Tab/Enter to accept suggestion (set text to suggestion value)
- [x] 7.4 Implement dismissal on any other typing (clear suggestion state)
- [x] 7.5 Only show ghost text for newly created empty syllable annotations
