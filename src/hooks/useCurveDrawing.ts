// Curve style constants
export const CURVE_NORMAL_COLOR = 'rgba(120, 120, 120, 0.4)';
export const CURVE_NORMAL_WIDTH = 1.5;
export const CURVE_HIGHLIGHT_COLOR = 'rgba(80, 80, 80, 0.8)';
export const CURVE_HIGHLIGHT_WIDTH = 2.5;

/**
 * Calculate bezier curve control points for a neume-to-syllable connection.
 * Creates a smooth downward arc.
 *
 * @param startX - Neume center X (normalized)
 * @param startY - Neume center Y (normalized)
 * @param endX - Closest point on syllable X (normalized)
 * @param endY - Closest point on syllable Y (normalized)
 */
export function calculateCurveControlPoints(
  startX: number,
  startY: number,
  endX: number,
  endY: number
): { cp1x: number; cp1y: number; cp2x: number; cp2y: number } {
  const deltaY = endY - startY;

  return {
    cp1x: startX,
    cp1y: startY + 0.4 * deltaY, // 40% down from start
    cp2x: endX,
    cp2y: startY + 0.6 * deltaY, // 60% down from start (40% up from end)
  };
}

/**
 * Draw a bezier curve from neume to syllable on the canvas.
 */
export function drawAssignmentCurve(
  ctx: CanvasRenderingContext2D,
  neumeX: number,
  neumeY: number,
  syllableEndX: number,
  syllableEndY: number,
  highlighted: boolean,
  toScreenX: (x: number) => number,
  toScreenY: (y: number) => number
): void {
  const { cp1x, cp1y, cp2x, cp2y } = calculateCurveControlPoints(
    neumeX,
    neumeY,
    syllableEndX,
    syllableEndY
  );

  ctx.beginPath();
  ctx.moveTo(toScreenX(neumeX), toScreenY(neumeY));
  ctx.bezierCurveTo(
    toScreenX(cp1x),
    toScreenY(cp1y),
    toScreenX(cp2x),
    toScreenY(cp2y),
    toScreenX(syllableEndX),
    toScreenY(syllableEndY)
  );

  ctx.strokeStyle = highlighted ? CURVE_HIGHLIGHT_COLOR : CURVE_NORMAL_COLOR;
  ctx.lineWidth = highlighted ? CURVE_HIGHLIGHT_WIDTH : CURVE_NORMAL_WIDTH;
  ctx.stroke();
}
