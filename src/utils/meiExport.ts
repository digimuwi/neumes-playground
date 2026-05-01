/**
 * MEI download for the user-facing export.
 *
 * The actual MEI generation lives in meiIO.ts; this module is a thin
 * wrapper that converts annotations to MEI bytes and triggers a browser
 * download.
 */

import { Annotation, LineBoundary } from '../state/types';
import { annotationsToMEI } from './meiIO';

export interface ImageDimensions {
  width: number;
  height: number;
}

/**
 * Extracts width/height from a base64 data URL by loading it into an Image element.
 */
export function getImageDimensions(dataUrl: string): Promise<ImageDimensions> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };
    img.src = dataUrl;
  });
}

/**
 * Generate canonical MEI XML for the given annotations.
 */
export function generateMEI(
  annotations: Annotation[],
  dimensions: ImageDimensions,
  lineBoundaries: LineBoundary[] = [],
  imageFilename: string = 'source-image.jpg',
): string {
  return annotationsToMEI(annotations, lineBoundaries, dimensions, imageFilename);
}

/**
 * Triggers a browser download of the given XML string.
 */
export function downloadMEI(xmlString: string, filename: string): void {
  const blob = new Blob([xmlString], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Main export function: gets image dimensions, generates MEI, and triggers download.
 */
export async function exportMEI(
  annotations: Annotation[],
  imageDataUrl: string,
  lineBoundaries: LineBoundary[] = [],
): Promise<void> {
  const dimensions = await getImageDimensions(imageDataUrl);
  const xml = generateMEI(annotations, dimensions, lineBoundaries);
  downloadMEI(xml, 'export.mei');
}
