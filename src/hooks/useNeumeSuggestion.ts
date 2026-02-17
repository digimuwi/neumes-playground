import { useState, useEffect, useRef } from 'react';
import { Annotation } from '../state/types';
import { binarizeRegion } from '../utils/imageProcessing';
import { classifyNeume } from '../utils/neumeClassifier';
import { polygonBounds } from '../utils/polygonUtils';

/**
 * Hook that provides neume type suggestions based on image classification.
 * Returns null if no suggestion available.
 */
export function useNeumeSuggestion(
  currentAnnotation: Annotation | null,
  isNewlyCreated: boolean,
  imageRef: React.RefObject<HTMLImageElement | null>,
  otsuThreshold: number | null,
  marginThreshold: number
): string | null {
  const [suggestion, setSuggestion] = useState<string | null>(null);
  // Track which annotation we're currently processing
  const processingForRef = useRef<string | null>(null);

  useEffect(() => {
    const annotationId = currentAnnotation?.id ?? null;

    // If annotation changed, clear suggestion and processing state
    if (processingForRef.current && processingForRef.current !== annotationId) {
      setSuggestion(null);
      processingForRef.current = null;
    }

    // Clear suggestion when no annotation selected
    if (!currentAnnotation) {
      setSuggestion(null);
      return;
    }

    // Already processing for this annotation - don't restart
    if (processingForRef.current === annotationId) {
      return;
    }

    // Only process for newly created neume annotations
    if (
      !isNewlyCreated ||
      currentAnnotation.type !== 'neume' ||
      !imageRef.current ||
      otsuThreshold === null
    ) {
      return;
    }

    // Start processing for this annotation
    processingForRef.current = annotationId;

    // Run classification (synchronously for now - it's fast enough)
    try {
      const img = imageRef.current;
      const bounds = polygonBounds(currentAnnotation.polygon);
      const rect = { x: bounds.minX, y: bounds.minY, width: bounds.maxX - bounds.minX, height: bounds.maxY - bounds.minY };

      // Create offscreen canvas to get image data
      const offscreenCanvas = document.createElement('canvas');
      offscreenCanvas.width = img.width;
      offscreenCanvas.height = img.height;
      const ctx = offscreenCanvas.getContext('2d');

      if (!ctx) {
        processingForRef.current = null;
        setSuggestion(null);
        return;
      }

      ctx.drawImage(img, 0, 0);
      const imageData = ctx.getImageData(0, 0, img.width, img.height);

      // Binarize the region
      // Add +10 bias to threshold (matching dudu.py) to capture more ink pixels
      const binaryImage = binarizeRegion(imageData, rect, otsuThreshold + 10, marginThreshold);

      if (binaryImage.width === 0 || binaryImage.height === 0) {
        processingForRef.current = null;
        setSuggestion(null);
        return;
      }

      // Classify
      const suggestions = classifyNeume(binaryImage);

      // Check if annotation is still current (user might have switched)
      if (processingForRef.current !== annotationId) {
        return;
      }

      if (suggestions.length > 0) {
        setSuggestion(suggestions[0].name);
      } else {
        setSuggestion(null);
      }
    } catch {
      if (processingForRef.current === annotationId) {
        processingForRef.current = null;
        setSuggestion(null);
      }
    }
  }, [currentAnnotation, isNewlyCreated, imageRef, otsuThreshold, marginThreshold]);

  return suggestion;
}
