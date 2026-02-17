import { Annotation } from '../state/types';
import { computeTextLines } from '../hooks/useTextLines';
import { getSyllablesInReadingOrder, stripHyphen } from './meiExport';

export interface ReconstructedText {
  /** Complete words joined by spaces */
  query: string;
  /** Incomplete word prefix (if last syllable ended with hyphen) */
  incompletePrefix: string;
  /** Number of syllables already entered for the incomplete word */
  incompleteSyllableCount: number;
}

/**
 * Reconstructs query text from syllable annotations preceding the given annotation.
 * Returns complete words as query, plus any incomplete word prefix.
 */
export function reconstructQueryText(
  annotations: Annotation[],
  newAnnotation: Annotation
): ReconstructedText {
  const empty: ReconstructedText = { query: '', incompletePrefix: '', incompleteSyllableCount: 0 };

  // Include the new annotation in text line computation
  const allAnnotations = [...annotations, newAnnotation];
  const textLines = computeTextLines(allAnnotations);
  const ordered = getSyllablesInReadingOrder(textLines);

  // Find position of new annotation
  const newIndex = ordered.findIndex((a) => a.id === newAnnotation.id);
  if (newIndex <= 0) {
    return empty;
  }

  // Get syllables before the new annotation
  const preceding = ordered.slice(0, newIndex);

  // Reconstruct words from syllables
  const words: string[] = [];
  let currentWord = '';
  let currentWordSyllableCount = 0;

  for (const syllable of preceding) {
    const text = syllable.text || '';
    if (text === '') continue;

    const endsWithHyphen = text.endsWith('-');
    currentWord += stripHyphen(text);
    currentWordSyllableCount++;

    if (!endsWithHyphen) {
      // Word complete
      words.push(currentWord);
      currentWord = '';
      currentWordSyllableCount = 0;
    }
  }

  return {
    query: words.join(' '),
    incompletePrefix: currentWord,
    incompleteSyllableCount: currentWordSyllableCount,
  };
}
