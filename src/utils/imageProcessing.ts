import { Rectangle } from '../state/types';
import { BinaryImage } from './neumeClassifier';
import { rectToPolygon, simplifyPolygon } from './polygonUtils';

const MARGIN_INTENSITY_CUTOFF = 30;
const MARGIN_PIXEL_THRESHOLD = 0.01; // 1% of image

export const OTSU_THRESHOLD_BIAS = 5;
const MIN_BBOX_SIZE = 4;
const BBOX_PADDING = 1;

/**
 * Detects if the image has black margins (scanner bed, book binding shadows).
 * Returns the margin threshold (30 if margins detected, 0 otherwise).
 */
export function detectMargins(imageData: ImageData): number {
  const { data, width, height } = imageData;
  const totalPixels = width * height;

  let darkPixelCount = 0;
  for (let i = 0; i < data.length; i += 4) {
    const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    if (gray < MARGIN_INTENSITY_CUTOFF) {
      darkPixelCount++;
    }
  }

  const darkRatio = darkPixelCount / totalPixels;
  return darkRatio > MARGIN_PIXEL_THRESHOLD ? MARGIN_INTENSITY_CUTOFF : 0;
}

/**
 * Computes the optimal threshold using Otsu's method.
 * Maximizes inter-class variance between foreground and background.
 * @param minIntensity - Optional minimum intensity to include in computation (excludes darker pixels)
 */
export function computeOtsuThreshold(imageData: ImageData, minIntensity: number = 0): number {
  const { data } = imageData;

  // Build grayscale histogram (256 bins), excluding pixels below minIntensity
  const histogram = new Array(256).fill(0);
  let includedPixels = 0;
  for (let i = 0; i < data.length; i += 4) {
    const gray = Math.round(0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]);
    if (gray >= minIntensity) {
      histogram[gray]++;
      includedPixels++;
    }
  }

  if (includedPixels === 0) {
    return 128; // Fallback if all pixels excluded
  }

  // Find threshold that maximizes inter-class variance
  let bestThreshold = minIntensity;
  let maxVariance = 0;

  let sumTotal = 0;
  for (let i = minIntensity; i < 256; i++) {
    sumTotal += i * histogram[i];
  }

  let sumBackground = 0;
  let weightBackground = 0;

  for (let t = minIntensity; t < 256; t++) {
    weightBackground += histogram[t];
    if (weightBackground === 0) continue;

    const weightForeground = includedPixels - weightBackground;
    if (weightForeground === 0) break;

    sumBackground += t * histogram[t];

    const meanBackground = sumBackground / weightBackground;
    const meanForeground = (sumTotal - sumBackground) / weightForeground;

    // Inter-class variance
    const variance =
      weightBackground * weightForeground * (meanBackground - meanForeground) ** 2;

    if (variance > maxVariance) {
      maxVariance = variance;
      bestThreshold = t;
    }
  }

  return bestThreshold;
}

/**
 * Tightens a rectangle to fit the foreground (ink) content.
 * Foreground is defined as pixels with intensity in [marginThreshold, threshold + thresholdBias).
 * Returns the original rectangle if no foreground pixels are found or if result is too small.
 * @param marginThreshold - Minimum intensity to consider as foreground (excludes black margins)
 * @param thresholdBias - Added to threshold to include fainter ink strokes
 */
export function tightenRectangle(
  rect: Rectangle,
  imageData: ImageData,
  threshold: number,
  marginThreshold: number = 0,
  thresholdBias: number = 0
): Rectangle {
  const { data, width, height } = imageData;

  // Convert normalized rect to pixel coordinates
  const pixelX = Math.floor(rect.x * width);
  const pixelY = Math.floor(rect.y * height);
  const pixelW = Math.ceil(rect.width * width);
  const pixelH = Math.ceil(rect.height * height);

  // Clamp to image bounds
  const startX = Math.max(0, pixelX);
  const startY = Math.max(0, pixelY);
  const endX = Math.min(width, pixelX + pixelW);
  const endY = Math.min(height, pixelY + pixelH);

  // Find bounding box of foreground pixels
  let minX = endX;
  let minY = endY;
  let maxX = startX;
  let maxY = startY;
  let foundForeground = false;

  const effectiveThreshold = threshold + thresholdBias;

  for (let y = startY; y < endY; y++) {
    for (let x = startX; x < endX; x++) {
      const idx = (y * width + x) * 4;
      // Convert to grayscale
      const gray = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];

      // Foreground = ink (darker than threshold but not as dark as margins)
      if (gray >= marginThreshold && gray < effectiveThreshold) {
        foundForeground = true;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }

  // No foreground found - return original rectangle
  if (!foundForeground) {
    return rect;
  }

  // Add padding (clamped to original rect bounds)
  minX = Math.max(startX, minX - BBOX_PADDING);
  minY = Math.max(startY, minY - BBOX_PADDING);
  maxX = Math.min(endX - 1, maxX + BBOX_PADDING);
  maxY = Math.min(endY - 1, maxY + BBOX_PADDING);

  // Check minimum size - if too small, return original rect
  const bboxWidth = maxX - minX + 1;
  const bboxHeight = maxY - minY + 1;
  if (bboxWidth < MIN_BBOX_SIZE || bboxHeight < MIN_BBOX_SIZE) {
    return rect;
  }

  // Convert back to normalized coordinates (include the pixel at maxX/maxY)
  return {
    x: minX / width,
    y: minY / height,
    width: bboxWidth / width,
    height: bboxHeight / height,
  };
}

const COLUMN_WIDTH = 8;
const CONTOUR_PADDING = 5;
const SIMPLIFY_TOLERANCE_PX = 4;
const MIN_CONTOUR_COLUMNS = 2;

/**
 * Tightens a rectangle to a contour polygon that hugs the foreground ink.
 * Scans vertical columns to find top/bottom foreground pixels, then connects
 * them into a closed polygon and simplifies with Douglas-Peucker.
 * Falls back to rectangular tightening if fewer than 2 non-empty columns.
 */
export function tightenToPolygon(
  rect: Rectangle,
  imageData: ImageData,
  threshold: number,
  marginThreshold: number = 0,
  thresholdBias: number = 0
): number[][] {
  const { data, width, height } = imageData;

  // First, tighten to bounding box (reuse existing logic for bounds)
  const tightRect = tightenRectangle(rect, imageData, threshold, marginThreshold, thresholdBias);

  // Convert tightened rect to pixel coordinates
  const pixelX = Math.floor(tightRect.x * width);
  const pixelY = Math.floor(tightRect.y * height);
  const pixelW = Math.ceil(tightRect.width * width);
  const pixelH = Math.ceil(tightRect.height * height);

  const startX = Math.max(0, pixelX);
  const startY = Math.max(0, pixelY);
  const endX = Math.min(width, pixelX + pixelW);
  const endY = Math.min(height, pixelY + pixelH);

  // Original rect vertical bounds for clamping padding
  const origPixelY = Math.floor(rect.y * height);
  const origEndY = Math.min(height, origPixelY + Math.ceil(rect.height * height));

  const effectiveThreshold = threshold + thresholdBias;

  // Scan vertical columns to find top/bottom foreground pixels
  const topEdge: number[][] = [];
  const bottomEdge: number[][] = [];

  for (let colStart = startX; colStart < endX; colStart += COLUMN_WIDTH) {
    const colEnd = Math.min(colStart + COLUMN_WIDTH, endX);
    const colCenterX = (colStart + colEnd) / 2;

    let colMinY = endY;
    let colMaxY = startY;
    let hasInk = false;

    for (let x = colStart; x < colEnd; x++) {
      for (let y = startY; y < endY; y++) {
        const idx = (y * width + x) * 4;
        const gray = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];

        if (gray >= marginThreshold && gray < effectiveThreshold) {
          hasInk = true;
          if (y < colMinY) colMinY = y;
          if (y > colMaxY) colMaxY = y;
        }
      }
    }

    if (hasInk) {
      // Apply padding, clamped to original rect bounds
      const paddedMinY = Math.max(origPixelY, colMinY - CONTOUR_PADDING);
      const paddedMaxY = Math.min(origEndY - 1, colMaxY + CONTOUR_PADDING);

      topEdge.push([colCenterX, paddedMinY]);
      bottomEdge.push([colCenterX, paddedMaxY]);
    }
  }

  // Fallback: fewer than 2 non-empty columns → rectangular polygon
  if (topEdge.length < MIN_CONTOUR_COLUMNS) {
    return rectToPolygon(tightRect);
  }

  // Build closed polygon: top edge left→right, bottom edge right→left
  const rawPolygon: number[][] = [
    ...topEdge,
    ...bottomEdge.reverse(),
  ];

  // Simplify and normalize to 0-1 coordinates
  const toleranceNorm = SIMPLIFY_TOLERANCE_PX / Math.max(width, height);
  const normalizedPolygon = rawPolygon.map(([x, y]) => [x / width, y / height]);
  return simplifyPolygon(normalizedPolygon, toleranceNorm);
}

/**
 * Creates a binary image from a region of an ImageData.
 * Foreground (1) = pixels with intensity in [marginThreshold, otsuThreshold)
 * Background (0) = all other pixels
 *
 * @param imageData - The full image data
 * @param rect - Normalized rectangle (0-1 coordinates)
 * @param otsuThreshold - Threshold for ink vs background
 * @param marginThreshold - Minimum intensity to consider (excludes scanner bed)
 */
export function binarizeRegion(
  imageData: ImageData,
  rect: Rectangle,
  otsuThreshold: number,
  marginThreshold: number = 0
): BinaryImage {
  const { data, width, height } = imageData;

  // Convert normalized rect to pixel coordinates
  const pixelX = Math.floor(rect.x * width);
  const pixelY = Math.floor(rect.y * height);
  const pixelW = Math.ceil(rect.width * width);
  const pixelH = Math.ceil(rect.height * height);

  // Clamp to image bounds
  const startX = Math.max(0, pixelX);
  const startY = Math.max(0, pixelY);
  const endX = Math.min(width, pixelX + pixelW);
  const endY = Math.min(height, pixelY + pixelH);

  const cropWidth = endX - startX;
  const cropHeight = endY - startY;

  if (cropWidth <= 0 || cropHeight <= 0) {
    return { data: new Uint8Array(0), width: 0, height: 0 };
  }

  const binaryData = new Uint8Array(cropWidth * cropHeight);

  for (let y = startY; y < endY; y++) {
    for (let x = startX; x < endX; x++) {
      const srcIdx = (y * width + x) * 4;
      const dstIdx = (y - startY) * cropWidth + (x - startX);

      // Convert to grayscale
      const gray = 0.299 * data[srcIdx] + 0.587 * data[srcIdx + 1] + 0.114 * data[srcIdx + 2];

      // Foreground = ink (darker than threshold but not as dark as margins)
      // 1 = foreground, 0 = background
      if (gray >= marginThreshold && gray < otsuThreshold) {
        binaryData[dstIdx] = 1;
      } else {
        binaryData[dstIdx] = 0;
      }
    }
  }

  return {
    data: binaryData,
    width: cropWidth,
    height: cropHeight,
  };
}
