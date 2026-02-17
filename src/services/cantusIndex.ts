import { syllabifyWord } from '../utils/latinSyllabifier';
import { Annotation } from '../state/types';
import { computeTextLines } from '../hooks/useTextLines';
import { polygonCenterX } from '../utils/polygonUtils';

export interface CantusChant {
  cid: string;
  fulltext: string;
  genre: string;
}

// In-memory cache keyed by query string
const cache = new Map<string, CantusChant[]>();

/**
 * Fetches chants from Cantus Index API.
 * Uses cache if available.
 */
async function fetchChantsRaw(query: string): Promise<CantusChant[]> {
  if (cache.has(query)) {
    return cache.get(query)!;
  }

  const encoded = encodeURIComponent(query);
  const url = `https://cantusindex.org/json-text/${encoded}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data: CantusChant[] = await response.json();
  cache.set(query, data);
  return data;
}

/**
 * Fetches chants from Cantus Index with progressive shortening.
 * If no results for full query, drops first word and retries.
 */
export async function fetchChants(query: string): Promise<CantusChant[]> {
  if (!query.trim()) {
    return [];
  }

  const words = query.trim().split(/\s+/);

  for (let i = 0; i < words.length; i++) {
    const shortenedQuery = words.slice(i).join(' ');
    const results = await fetchChantsRaw(shortenedQuery);

    if (results.length > 0) {
      return results;
    }
  }

  return [];
}

/**
 * Extracts the next word from chant results.
 * If incompletePrefix is provided, finds words starting with that prefix.
 * Otherwise, finds the word after the query string.
 */
export function extractNextWord(
  chants: CantusChant[],
  query: string,
  incompletePrefix: string = ''
): string | null {
  if (chants.length === 0) {
    return null;
  }

  const queryLower = query.toLowerCase();
  const prefixLower = incompletePrefix.toLowerCase();
  const nextWords = new Map<string, number>();
  let firstWord: string | null = null;

  for (const chant of chants) {
    const fulltext = chant.fulltext;
    const fulltextLower = fulltext.toLowerCase();

    // Find where the query ends in the fulltext
    let searchStart = 0;
    if (query.trim()) {
      const queryIndex = fulltextLower.indexOf(queryLower);
      if (queryIndex === -1) continue;
      searchStart = queryIndex + query.length;
    }

    // Get text after the query
    const afterQuery = fulltext.slice(searchStart).trim();
    if (!afterQuery) continue;

    // Split into words
    const words = afterQuery.split(/\s+/);

    let targetWord: string | null = null;

    if (prefixLower) {
      // Find a word that starts with the incomplete prefix
      for (const word of words) {
        const cleaned = word.replace(/^[^\w]+|[^\w]+$/g, '');
        if (cleaned.toLowerCase().startsWith(prefixLower)) {
          targetWord = cleaned;
          break;
        }
      }
    } else {
      // No prefix - just take the first word after query
      const firstWordRaw = words[0];
      if (firstWordRaw) {
        targetWord = firstWordRaw.replace(/^[^\w]+|[^\w]+$/g, '');
      }
    }

    if (!targetWord) continue;

    // Track first occurrence for tie-breaking
    if (firstWord === null) {
      firstWord = targetWord;
    }

    nextWords.set(targetWord, (nextWords.get(targetWord) || 0) + 1);
  }

  if (nextWords.size === 0) {
    return null;
  }

  // Find most common
  let maxCount = 0;
  let maxWord = firstWord;

  for (const [word, count] of nextWords) {
    if (count > maxCount) {
      maxCount = count;
      maxWord = word;
    }
  }

  return maxWord;
}

/**
 * Syllabifies an entire chant fulltext into formatted syllables.
 * Each syllable gets a trailing hyphen unless it's the last syllable of a word.
 */
export async function syllabifyFulltext(fulltext: string): Promise<string[]> {
  const words = fulltext.trim().split(/\s+/).filter(w => w.length > 0);
  const result: string[] = [];

  for (const word of words) {
    // Clean punctuation from word
    const cleaned = word.replace(/^[^\w]+|[^\w]+$/g, '');
    if (!cleaned) continue;

    const syllables = await syllabifyWord(cleaned);

    for (let i = 0; i < syllables.length; i++) {
      const isLastSyllable = i === syllables.length - 1;
      result.push(isLastSyllable ? syllables[i] : `${syllables[i]}-`);
    }
  }

  return result;
}

/**
 * Collects text from syllable annotations in reading order.
 * Strips hyphens and joins syllables into words/text.
 */
export function collectQueryText(annotations: Annotation[]): string {
  const textLines = computeTextLines(annotations);
  const syllableTexts: string[] = [];

  for (const line of textLines) {
    // Sort syllables within the line by x position (left to right)
    const sortedSyllables = [...line.syllables].sort((a, b) => {
      return polygonCenterX(a.polygon) - polygonCenterX(b.polygon);
    });

    for (const syllable of sortedSyllables) {
      const text = syllable.text?.trim();
      if (text) {
        // Strip trailing hyphen and add to result
        syllableTexts.push(text.endsWith('-') ? text.slice(0, -1) : text);
      }
    }
  }

  // Join all syllables - consecutive syllables that were hyphenated
  // are now without hyphens, so we need to reconstruct words
  // The simplest approach: join all and let Cantus Index handle matching
  return syllableTexts.join(' ');
}

/**
 * Looks up Cantus ID from annotations.
 * Returns the matching chants from Cantus Index.
 */
export async function lookupCantusId(annotations: Annotation[]): Promise<CantusChant[]> {
  const queryText = collectQueryText(annotations);
  if (!queryText.trim()) {
    return [];
  }
  return fetchChants(queryText);
}
