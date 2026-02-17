## Context

The current Cantus suggestions implementation makes an API call for every new syllable annotation. Since the API returns full chant texts (`fulltext` field), we already have all the information needed to predict subsequent syllables without re-querying. When a user accepts suggestions sequentially (the common case), we're making redundant API calls.

Current flow:
1. User creates syllable → query "Do" → API call → suggest "mi-"
2. User accepts → query "Domi" → API call → suggest "ne"
3. User accepts → query "Domine" → API call → suggest "non"

Each query is different, so the per-query cache doesn't help.

## Goals / Non-Goals

**Goals:**
- Reduce API calls to one per chant when user accepts suggestions sequentially
- Maintain same user-visible behavior (suggestions still appear correctly)
- Keep the optimization invisible - no UI changes

**Non-Goals:**
- Persisting prediction cache across sessions (in-memory only)
- Prefetching multiple chants
- Changing how the top chant is selected

## Decisions

### Decision 1: Cache syllabified chant prediction, not raw API response

**Choice:** After picking the top chant, syllabify its entire `fulltext` and cache the syllable array with a position pointer.

**Alternatives considered:**
- Cache raw API responses (current approach) - doesn't help because queries change
- Cache multiple chants - adds complexity, unclear benefit

**Rationale:** Chants are short. Syllabifying the whole thing upfront is cheap and gives us everything we need to serve subsequent suggestions instantly.

### Decision 2: Invalidate on divergence only

**Choice:** Invalidate the cached prediction when user types something other than the current suggestion. Don't invalidate on accept.

**Alternatives considered:**
- Invalidate after N syllables - arbitrary, unnecessary
- Never invalidate - would lock user into wrong chant

**Rationale:** If user is accepting suggestions, they're following the predicted chant. If they type something different, they know what they want - refetch with their input.

### Decision 3: Return null when prediction exhausted

**Choice:** When position exceeds syllable array length, return null (no suggestion).

**Alternatives considered:**
- Refetch with recent context - might find continuation, but adds complexity
- Loop back to start - makes no sense

**Rationale:** Running out means they've annotated the whole chant. Natural stopping point.

### Decision 4: Store prediction state in useSuggestion hook

**Choice:** Keep prediction cache state (syllables, position, anchor query) as refs in the `useSuggestion` hook rather than in the cantusIndex service.

**Rationale:** The hook already manages suggestion lifecycle. Adding prediction state there keeps related logic together and avoids coupling the service to React-specific concerns.

## Risks / Trade-offs

**[Risk] Stale prediction if user edits earlier syllables** → Cache is invalidated when user types anything different than the suggestion. Editing an earlier syllable and returning will trigger a refetch with updated context.

**[Risk] Memory usage for long chants** → Chants are short (typically <100 syllables). Memory is negligible.

**[Trade-off] First suggestion still requires API call** → Acceptable. We're optimizing the sequential case, not eliminating all API calls.
