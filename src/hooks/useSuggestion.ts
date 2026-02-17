import { useState, useEffect, useRef } from 'react';
import { Annotation } from '../state/types';
import { reconstructQueryText } from '../utils/textReconstruction';
import { fetchChants, syllabifyFulltext } from '../services/cantusIndex';

interface PredictionCache {
  syllables: string[];
  position: number;
}

/**
 * Hook that provides syllable suggestions based on Cantus Index.
 * Returns null if no suggestion available or on any error.
 */
export function useSuggestion(
  annotations: Annotation[],
  currentAnnotation: Annotation | null,
  isNewlyCreated: boolean
): string | null {
  const [suggestion, setSuggestion] = useState<string | null>(null);
  // Track which annotation we're currently fetching for
  const fetchingForRef = useRef<string | null>(null);
  // Cancellation flag as ref so it persists across effect re-runs
  const cancelledRef = useRef(false);
  // Prediction cache for serving suggestions without API calls
  const predictionCacheRef = useRef<PredictionCache | null>(null);
  // Track the last suggestion we provided (for divergence detection)
  const lastSuggestionRef = useRef<string | null>(null);

  useEffect(() => {
    const annotationId = currentAnnotation?.id ?? null;

    // If annotation changed, cancel any in-flight fetch and clear suggestion
    if (fetchingForRef.current && fetchingForRef.current !== annotationId) {
      cancelledRef.current = true;
      setSuggestion(null);
      fetchingForRef.current = null;
    }

    // Clear suggestion when no annotation selected
    if (!currentAnnotation) {
      setSuggestion(null);
      return;
    }

    // Already fetching for this annotation - don't restart
    if (fetchingForRef.current === annotationId) {
      return;
    }

    // Only fetch for newly created empty syllable annotations
    if (
      !isNewlyCreated ||
      currentAnnotation.type !== 'syllable' ||
      (currentAnnotation.text && currentAnnotation.text.length > 0)
    ) {
      return;
    }

    // Reconstruct query text from preceding syllables
    const { query, incompletePrefix, incompleteSyllableCount } = reconstructQueryText(annotations, currentAnnotation);

    // Detect divergence: check what the previous annotation's text is
    // If we had a suggestion and the user typed something different, invalidate cache
    if (lastSuggestionRef.current && predictionCacheRef.current) {
      const prevSuggestion = lastSuggestionRef.current;
      // Find the most recent syllable with text (the one that would have our suggestion)
      const syllablesWithText = annotations
        .filter(a => a.type === 'syllable' && a.text && a.text.length > 0);

      if (syllablesWithText.length > 0) {
        const lastFilledSyllable = syllablesWithText[syllablesWithText.length - 1];
        if (lastFilledSyllable.text !== prevSuggestion) {
          // User typed something different - invalidate cache
          predictionCacheRef.current = null;
        }
      }
    }

    // Check if we can serve from prediction cache
    if (predictionCacheRef.current) {
      const cache = predictionCacheRef.current;

      // Handle prediction exhaustion
      if (cache.position >= cache.syllables.length) {
        predictionCacheRef.current = null;
        setSuggestion(null);
        lastSuggestionRef.current = null;
        // Don't return - fall through to fetch with new context
      } else {
        // Serve from cache
        const nextSuggestion = cache.syllables[cache.position];
        cache.position++;
        setSuggestion(nextSuggestion);
        lastSuggestionRef.current = nextSuggestion;
        fetchingForRef.current = annotationId; // Mark as handled
        return;
      }
    }

    if (!query && !incompletePrefix) {
      fetchingForRef.current = null;
      setSuggestion(null);
      lastSuggestionRef.current = null;
      return;
    }

    // Require at least 2 complete words before making API request
    // to avoid overly broad result sets
    const wordCount = query ? query.trim().split(/\s+/).length : 0;
    if (wordCount < 2) {
      fetchingForRef.current = null;
      setSuggestion(null);
      lastSuggestionRef.current = null;
      return;
    }

    // Start fetching for this annotation
    fetchingForRef.current = annotationId;
    cancelledRef.current = false;

    async function doFetch() {
      try {
        // Fetch chants from Cantus Index
        const searchQuery = query;
        const chants = await fetchChants(searchQuery);
        if (cancelledRef.current) {
          return;
        }

        if (chants.length === 0) {
          fetchingForRef.current = null;
          setSuggestion(null);
          lastSuggestionRef.current = null;
          return;
        }

        // Pick the top chant and syllabify its entire fulltext
        // Use the first chant that contains our query
        const queryLower = query.toLowerCase();
        const topChant = chants.find(c =>
          c.fulltext.toLowerCase().includes(queryLower)
        ) || chants[0];

        const allSyllables = await syllabifyFulltext(topChant.fulltext);
        if (cancelledRef.current) return;

        if (allSyllables.length === 0) {
          fetchingForRef.current = null;
          setSuggestion(null);
          lastSuggestionRef.current = null;
          return;
        }

        // Find the starting position in the syllable array
        // We need to skip syllables that correspond to already-entered text
        // Count syllables from complete words + incomplete syllables
        let startPosition = 0;

        // Count syllables in complete words
        if (query) {
          const queryWords = query.split(/\s+/);
          for (const word of queryWords) {
            // Find matching word in fulltext and count its syllables
            const wordLower = word.toLowerCase();
            let found = false;
            for (let i = startPosition; i < allSyllables.length; i++) {
              // Build word from syllables starting at i
              let builtWord = '';
              let j = i;
              while (j < allSyllables.length) {
                const syl = allSyllables[j];
                const isLast = !syl.endsWith('-');
                builtWord += syl.replace(/-$/, '');
                j++;
                if (isLast) break;
              }
              if (builtWord.toLowerCase() === wordLower) {
                startPosition = j;
                found = true;
                break;
              }
            }
            if (!found) break;
          }
        }

        // Add incomplete syllable count
        startPosition += incompleteSyllableCount;

        if (startPosition >= allSyllables.length) {
          fetchingForRef.current = null;
          setSuggestion(null);
          lastSuggestionRef.current = null;
          return;
        }

        // Populate prediction cache
        predictionCacheRef.current = {
          syllables: allSyllables,
          position: startPosition + 1, // Will be used for NEXT suggestion
        };

        // Return current suggestion
        const currentSuggestion = allSyllables[startPosition];
        setSuggestion(currentSuggestion);
        lastSuggestionRef.current = currentSuggestion;
      } catch {
        if (!cancelledRef.current) {
          fetchingForRef.current = null;
          setSuggestion(null);
          lastSuggestionRef.current = null;
        }
      }
    }

    doFetch();
  }, [annotations, currentAnnotation, isNewlyCreated]);

  return suggestion;
}
