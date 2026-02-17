import { hyphenate } from 'hyphen/la-x-liturgic';

/**
 * Syllabifies a Latin word using liturgical patterns.
 */
export async function syllabifyWord(word: string): Promise<string[]> {
  if (!word.trim()) {
    return [];
  }

  // Hyphenate with visible hyphen character
  const hyphenated = await hyphenate(word, { hyphenChar: '-' });

  // Split on hyphen to get syllables
  return hyphenated.split('-').filter((s) => s.length > 0);
}

/**
 * Formats syllables as a suggestion with appropriate hyphen.
 * First syllable of multi-syllable word gets trailing hyphen.
 * Single-syllable word has no hyphen.
 */
export function formatSuggestion(syllables: string[]): string {
  if (syllables.length === 0) {
    return '';
  }

  const firstSyllable = syllables[0];

  // Add hyphen if there are more syllables
  if (syllables.length > 1) {
    return `${firstSyllable}-`;
  }

  return firstSyllable;
}
