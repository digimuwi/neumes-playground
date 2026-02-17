## 1. Prediction Cache Infrastructure

- [x] 1.1 Add `syllabifyFulltext` function to cantusIndex.ts that takes a chant fulltext and returns array of formatted syllables (with hyphens)
- [x] 1.2 Add prediction cache type and refs to useSuggestion hook (syllables array, position, anchor query)

## 2. Cache Population

- [x] 2.1 After picking top chant, syllabify entire fulltext and populate prediction cache
- [x] 2.2 Set initial position to the appropriate syllable index based on current context (incompletePrefix handling)

## 3. Cache Utilization

- [x] 3.1 Check for valid prediction cache before making API call
- [x] 3.2 Return syllable at current position from cache when available
- [x] 3.3 Advance position after suggestion is used (detect accept vs type)

## 4. Cache Invalidation

- [x] 4.1 Detect divergence: user typed something different than the suggestion
- [x] 4.2 Invalidate prediction cache on divergence
- [x] 4.3 Handle prediction exhaustion (position >= syllables.length) by returning null

## 5. Query Constraints

- [x] 5.1 Require at least 2 complete words before making API request

## 6. Testing (manual - no test framework)

- [x] 6.1 Test sequential acceptance serves from cache without API calls
- [x] 6.2 Test divergence triggers cache invalidation and fresh fetch
- [x] 6.3 Test prediction exhaustion returns null
