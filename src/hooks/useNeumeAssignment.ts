import { useMemo } from 'react';
import { Annotation } from '../state/types';
import { useTextLines, TextLine } from './useTextLines';
import { polygonMinX, polygonBottomY, polygonCenterX } from '../utils/polygonUtils';

/**
 * Pure function that computes neume-to-syllable assignments based on spatial relationships.
 * Returns a Map from neumeId to syllableId.
 */
export function computeNeumeAssignments(
  annotations: Annotation[],
  textLines: TextLine[]
): Map<string, string> {
  const assignments = new Map<string, string>();

  if (textLines.length === 0) {
    return assignments;
  }

  const neumes = annotations.filter((a) => a.type === 'neume');

  for (const neume of neumes) {
    const neumeX = polygonMinX(neume.polygon);
    const neumeY = polygonBottomY(neume.polygon);

    // Find owning text line
    const owningLine = findOwningLine(neumeX, neumeY, textLines);
    if (!owningLine) continue;

    // Find syllable within the line
    const syllable = findClosestSyllable(neumeX, owningLine);
    if (syllable) {
      assignments.set(neume.id, syllable.id);
    }
  }

  return assignments;
}

/**
 * React hook that computes neume-to-syllable assignments based on spatial relationships.
 * Returns a Map from neumeId to syllableId.
 */
export function useNeumeAssignment(
  annotations: Annotation[]
): Map<string, string> {
  const textLines = useTextLines(annotations);

  return useMemo(
    () => computeNeumeAssignments(annotations, textLines),
    [annotations, textLines]
  );
}

/**
 * Find the text line that "owns" the neume based on its position.
 * A neume belongs to the first line (top-to-bottom) where
 * lineY(neumeX) >= neumeY.
 */
function findOwningLine(
  neumeX: number,
  neumeY: number,
  lines: TextLine[]
): TextLine | null {
  if (lines.length === 0) return null;

  for (const line of lines) {
    const lineYAtNeume = line.slope * neumeX + line.intercept;
    if (neumeY <= lineYAtNeume) {
      return line;
    }
  }

  // Neume is below all lines - belongs to last line
  return lines[lines.length - 1];
}

/**
 * Find the closest syllable to the left of the neume within the text line.
 * Exception: if neume is left of all syllables, use leftmost syllable.
 */
function findClosestSyllable(
  neumeX: number,
  line: TextLine
): Annotation | null {
  if (line.syllables.length === 0) return null;

  // Sort syllables by centerX
  const sortedSyllables = [...line.syllables].sort((a, b) => {
    return polygonCenterX(a.polygon) - polygonCenterX(b.polygon);
  });

  // Find syllables whose left edge is at or before the neume position
  const syllablesLeft = sortedSyllables.filter((s) => {
    return polygonMinX(s.polygon) <= neumeX;
  });

  if (syllablesLeft.length > 0) {
    // Return the rightmost of the left syllables (closest to neume)
    return syllablesLeft[syllablesLeft.length - 1];
  }

  // Exception: neume is left of all syllables - assign to leftmost
  return sortedSyllables[0];
}
