/**
 * Utility functions for polygon geometry operations.
 * All polygons are represented as number[][] (array of [x, y] coordinate pairs).
 */

export interface PolygonBounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

interface ImageDimensions {
  width: number;
  height: number;
}

/**
 * Compute the axis-aligned bounding rectangle of a polygon.
 */
export function polygonBounds(poly: number[][]): PolygonBounds {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const [x, y] of poly) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }

  return { minX, minY, maxX, maxY };
}

/**
 * Compute the horizontal center of a polygon's bounding box.
 */
export function polygonCenterX(poly: number[][]): number {
  const { minX, maxX } = polygonBounds(poly);
  return (minX + maxX) / 2;
}

/**
 * Compute the bottom Y (maximum Y) of a polygon.
 */
export function polygonBottomY(poly: number[][]): number {
  return polygonBounds(poly).maxY;
}

/**
 * Compute the left edge (minimum X) of a polygon.
 */
export function polygonMinX(poly: number[][]): number {
  return polygonBounds(poly).minX;
}

/**
 * Ray casting algorithm for point-in-polygon test.
 */
export function pointInPolygon(x: number, y: number, poly: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i][0], yi = poly[i][1];
    const xj = poly[j][0], yj = poly[j][1];

    const intersect =
      yi > y !== yj > y &&
      x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;

    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * Find the closest point on a polygon's edges to a given external point.
 */
export function closestPointOnPolygon(
  px: number,
  py: number,
  poly: number[][]
): { x: number; y: number } {
  let bestDist = Infinity;
  let bestPoint = { x: poly[0][0], y: poly[0][1] };

  for (let i = 0; i < poly.length; i++) {
    const j = (i + 1) % poly.length;
    const ax = poly[i][0], ay = poly[i][1];
    const bx = poly[j][0], by = poly[j][1];

    // Project point onto line segment
    const dx = bx - ax;
    const dy = by - ay;
    const lenSq = dx * dx + dy * dy;

    let t = 0;
    if (lenSq > 0) {
      t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lenSq));
    }

    const cx = ax + t * dx;
    const cy = ay + t * dy;
    const dist = (px - cx) * (px - cx) + (py - cy) * (py - cy);

    if (dist < bestDist) {
      bestDist = dist;
      bestPoint = { x: cx, y: cy };
    }
  }

  return bestPoint;
}

/**
 * Convert polygon from pixel coordinates to normalized (0-1) coordinates.
 */
export function normalizePolygon(
  poly: number[][],
  dimensions: ImageDimensions
): number[][] {
  return poly.map(([x, y]) => [x / dimensions.width, y / dimensions.height]);
}

/**
 * Convert polygon from normalized (0-1) coordinates to pixel coordinates.
 */
export function denormalizePolygon(
  poly: number[][],
  dimensions: ImageDimensions
): number[][] {
  return poly.map(([x, y]) => [
    Math.round(x * dimensions.width),
    Math.round(y * dimensions.height),
  ]);
}

/**
 * Simplify a polygon using the Douglas-Peucker algorithm.
 * Removes vertices that are within `tolerance` of the line between their neighbors.
 */
export function simplifyPolygon(poly: number[][], tolerance: number): number[][] {
  if (poly.length <= 3) return poly;

  // Find the point farthest from the line between first and last
  let maxDist = 0;
  let maxIdx = 0;
  const first = poly[0];
  const last = poly[poly.length - 1];

  for (let i = 1; i < poly.length - 1; i++) {
    const dist = perpendicularDistance(poly[i], first, last);
    if (dist > maxDist) {
      maxDist = dist;
      maxIdx = i;
    }
  }

  if (maxDist > tolerance) {
    const left = simplifyPolygon(poly.slice(0, maxIdx + 1), tolerance);
    const right = simplifyPolygon(poly.slice(maxIdx), tolerance);
    return left.slice(0, -1).concat(right);
  } else {
    return [first, last];
  }
}

function perpendicularDistance(point: number[], lineStart: number[], lineEnd: number[]): number {
  const dx = lineEnd[0] - lineStart[0];
  const dy = lineEnd[1] - lineStart[1];
  const lenSq = dx * dx + dy * dy;

  if (lenSq === 0) {
    const ex = point[0] - lineStart[0];
    const ey = point[1] - lineStart[1];
    return Math.sqrt(ex * ex + ey * ey);
  }

  const t = ((point[0] - lineStart[0]) * dx + (point[1] - lineStart[1]) * dy) / lenSq;
  const projX = lineStart[0] + t * dx;
  const projY = lineStart[1] + t * dy;
  const ex = point[0] - projX;
  const ey = point[1] - projY;
  return Math.sqrt(ex * ex + ey * ey);
}

/**
 * Convert a rectangle {x, y, width, height} to a 4-corner polygon.
 */
export function rectToPolygon(rect: {
  x: number;
  y: number;
  width: number;
  height: number;
}): number[][] {
  return [
    [rect.x, rect.y],
    [rect.x + rect.width, rect.y],
    [rect.x + rect.width, rect.y + rect.height],
    [rect.x, rect.y + rect.height],
  ];
}
