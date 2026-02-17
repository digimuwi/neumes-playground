## Why

Currently, each new syllable annotation triggers a fresh API call to Cantus Index, even when the user is simply accepting suggestions sequentially. Since the API returns full chant texts, we already have all the information needed to predict subsequent syllables without re-querying.

## What Changes

- Cache the entire syllabified chant text after the first API call
- Serve subsequent suggestions from the cache by advancing a position pointer
- Only refetch when the user diverges from the predicted sequence (types something different than the suggestion)
- Return null when the cached prediction is exhausted (end of chant)

## Capabilities

### New Capabilities

None - this is an optimization of existing behavior.

### Modified Capabilities

- `cantus-suggestions`: Changes caching strategy from per-query response caching to per-chant prediction caching. Adds cache invalidation on user divergence.

## Impact

- `src/services/cantusIndex.ts` - Add prediction caching logic
- `src/hooks/useSuggestion.ts` - Track prediction state and detect divergence
- Significantly reduces API calls during sequential annotation workflows
- No user-visible behavior changes (optimization only)
