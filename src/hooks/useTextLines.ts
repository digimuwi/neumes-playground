import { useMemo } from 'react';
import { Annotation } from '../state/types';
import { polygonCenterX, polygonBottomY } from '../utils/polygonUtils';

export interface TextLine {
  slope: number;
  intercept: number;
  syllables: Annotation[];
}

interface SyllableWithMetrics {
  annotation: Annotation;
  centerX: number;
  bottomY: number;
}

/**
 * Compute perpendicular distance from a point to a line y = mx + b.
 * Formula: |y₀ - (m·x₀ + b)| / √(m² + 1)
 */
function perpendicularDistance(
  x: number,
  y: number,
  slope: number,
  intercept: number
): number {
  const numerator = Math.abs(y - (slope * x + intercept));
  const denominator = Math.sqrt(slope * slope + 1);
  return numerator / denominator;
}

/**
 * Cluster state that tracks both the syllables and the current line fit.
 */
interface ClusterState {
  syllables: SyllableWithMetrics[];
  slope: number;
  intercept: number;
}

/**
 * Pure function that clusters syllables into text lines using perpendicular
 * distance to fitted lines. This correctly handles tilted handwriting where
 * Y-coordinates from different lines may interleave.
 */
export function computeTextLines(annotations: Annotation[]): TextLine[] {
  const syllables = annotations.filter((a) => a.type === 'syllable');
  if (syllables.length === 0) return [];

  // Compute metrics for each syllable
  const syllablesWithMetrics: SyllableWithMetrics[] = syllables.map((s) => ({
    annotation: s,
    centerX: polygonCenterX(s.polygon),
    bottomY: polygonBottomY(s.polygon),
  }));

  // Sort by bottomY as initial ordering heuristic
  syllablesWithMetrics.sort((a, b) => a.bottomY - b.bottomY);

  // Perpendicular distance threshold for assigning to a line
  const PERP_THRESHOLD = 0.02;
  // Y-distance threshold for single-element clusters
  const Y_THRESHOLD = 0.03;

  const clusters: ClusterState[] = [];

  for (const syllable of syllablesWithMetrics) {
    let bestClusterIdx = -1;
    let bestDistance = Infinity;

    // Check ALL existing clusters to find the best fit
    for (let i = 0; i < clusters.length; i++) {
      const cluster = clusters[i];
      let distance: number;

      if (cluster.syllables.length >= 2) {
        // Use perpendicular distance to the fitted line
        distance = perpendicularDistance(
          syllable.centerX,
          syllable.bottomY,
          cluster.slope,
          cluster.intercept
        );
        if (distance < bestDistance && distance <= PERP_THRESHOLD) {
          bestDistance = distance;
          bestClusterIdx = i;
        }
      } else {
        // Single-element cluster: use Y-distance
        distance = Math.abs(syllable.bottomY - cluster.intercept);
        if (distance < bestDistance && distance <= Y_THRESHOLD) {
          bestDistance = distance;
          bestClusterIdx = i;
        }
      }
    }

    if (bestClusterIdx >= 0) {
      // Add to the best-fitting cluster and refit the line
      const cluster = clusters[bestClusterIdx];
      cluster.syllables.push(syllable);

      if (cluster.syllables.length >= 2) {
        const fit = fitLinearRegression(cluster.syllables);
        cluster.slope = fit.slope;
        cluster.intercept = fit.intercept;
      }
    } else {
      // Start a new cluster
      clusters.push({
        syllables: [syllable],
        slope: 0,
        intercept: syllable.bottomY,
      });
    }
  }

  // Convert to TextLine format
  const textLines: TextLine[] = clusters.map((cluster) => ({
    slope: cluster.slope,
    intercept: cluster.intercept,
    syllables: cluster.syllables.map((s) => s.annotation),
  }));

  // Inherit slopes for single-syllable lines
  inheritSlopes(textLines);

  // Sort by intercept (top-to-bottom)
  textLines.sort((a, b) => a.intercept - b.intercept);

  return textLines;
}

/**
 * React hook that clusters syllables into text lines based on bottom Y positions,
 * fits linear models to handle tilted handwriting.
 */
export function useTextLines(annotations: Annotation[]): TextLine[] {
  return useMemo(() => computeTextLines(annotations), [annotations]);
}

/**
 * Simple linear regression: y = mx + b
 * Using least squares method.
 */
function fitLinearRegression(
  points: SyllableWithMetrics[]
): { slope: number; intercept: number } {
  const n = points.length;
  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumX2 = 0;

  for (const p of points) {
    sumX += p.centerX;
    sumY += p.bottomY;
    sumXY += p.centerX * p.bottomY;
    sumX2 += p.centerX * p.centerX;
  }

  const denominator = n * sumX2 - sumX * sumX;
  if (Math.abs(denominator) < 1e-10) {
    // Vertical line or all same X - use horizontal
    return { slope: 0, intercept: sumY / n };
  }

  const slope = (n * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / n;

  return { slope, intercept };
}

/**
 * For single-syllable lines, inherit slope from the nearest multi-syllable line.
 */
function inheritSlopes(lines: TextLine[]): void {
  // Find lines with multiple syllables (these have valid slopes)
  const multiSyllableLines = lines.filter((l) => l.syllables.length >= 2);

  if (multiSyllableLines.length === 0) {
    // All lines are single-syllable - keep slope = 0
    return;
  }

  for (const line of lines) {
    if (line.syllables.length === 1) {
      // Find nearest multi-syllable line by intercept distance
      let nearest = multiSyllableLines[0];
      let minDist = Math.abs(line.intercept - nearest.intercept);

      for (const other of multiSyllableLines) {
        const dist = Math.abs(line.intercept - other.intercept);
        if (dist < minDist) {
          minDist = dist;
          nearest = other;
        }
      }

      // Inherit slope and recompute intercept
      const syllable = line.syllables[0];
      const centerX = polygonCenterX(syllable.polygon);
      const bottomY = polygonBottomY(syllable.polygon);

      line.slope = nearest.slope;
      line.intercept = bottomY - nearest.slope * centerX;
    }
  }
}
