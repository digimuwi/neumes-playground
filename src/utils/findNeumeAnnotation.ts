import { Annotation } from '../state/types';
import { polygonBounds } from './polygonUtils';

/**
 * Find the annotation that best matches a NeumeCrop (pixel-space bbox) among a
 * loaded set of annotations (normalized polygons). Matches on neume type, then
 * picks the closest centroid.
 */
export function findNeumeAnnotation(
  annotations: Annotation[],
  neumeType: string,
  bbox: { x: number; y: number; width: number; height: number },
  imageWidth: number,
  imageHeight: number,
): Annotation | null {
  if (imageWidth <= 0 || imageHeight <= 0) return null;

  const targetCx = (bbox.x + bbox.width / 2) / imageWidth;
  const targetCy = (bbox.y + bbox.height / 2) / imageHeight;

  let best: Annotation | null = null;
  let bestDist = Infinity;

  for (const a of annotations) {
    if (a.type !== 'neume' || a.neumeType !== neumeType) continue;
    const b = polygonBounds(a.polygon);
    const cx = (b.minX + b.maxX) / 2;
    const cy = (b.minY + b.maxY) / 2;
    const d = Math.hypot(cx - targetCx, cy - targetCy);
    if (d < bestDist) {
      bestDist = d;
      best = a;
    }
  }

  return best;
}
