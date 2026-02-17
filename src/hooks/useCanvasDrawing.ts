import { useRef, useState, useCallback, useEffect } from 'react';
import { Rectangle, Annotation } from '../state/types';
import { pointInPolygon } from '../utils/polygonUtils';

interface DrawingState {
  isDrawing: boolean;
  startX: number;
  startY: number;
  currentRect: Rectangle | null;
}

interface UseCanvasDrawingOptions {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  imageWidth: number;
  imageHeight: number;
  annotations: Annotation[];
  onRectangleDrawn: (rect: Rectangle) => void;
  onAnnotationClicked: (id: string | null, isModifierHeld: boolean) => void;
  onAnnotationHovered?: (id: string | null) => void;
  zoom: number;
  panX: number;
  panY: number;
  isSpaceHeld: boolean;
  onPan: (deltaX: number, deltaY: number) => void;
  onPanStart: () => void;
  onPanEnd: () => void;
  onResetView: () => void;
}

export function useCanvasDrawing({
  canvasRef,
  imageWidth,
  imageHeight,
  annotations,
  onRectangleDrawn,
  onAnnotationClicked,
  onAnnotationHovered,
  zoom,
  panX,
  panY,
  isSpaceHeld,
  onPan,
  onPanStart,
  onPanEnd,
  onResetView,
}: UseCanvasDrawingOptions) {
  const drawingStateRef = useRef<DrawingState>({
    isDrawing: false,
    startX: 0,
    startY: 0,
    currentRect: null,
  });
  const [previewRect, setPreviewRect] = useState<Rectangle | null>(null);
  const panStartRef = useRef<{ x: number; y: number } | null>(null);

  const getCanvasCoordinates = useCallback(
    (e: MouseEvent): { x: number; y: number } | null => {
      const canvas = canvasRef.current;
      if (!canvas || imageWidth === 0 || imageHeight === 0) return null;

      const rect = canvas.getBoundingClientRect();
      const containerWidth = canvas.width;
      const containerHeight = canvas.height;

      // Calculate base image dimensions (at zoom=1)
      const imgAspect = imageWidth / imageHeight;
      const containerAspect = containerWidth / containerHeight;

      let baseWidth: number;
      let baseHeight: number;

      if (imgAspect > containerAspect) {
        baseWidth = containerWidth;
        baseHeight = containerWidth / imgAspect;
      } else {
        baseHeight = containerHeight;
        baseWidth = containerHeight * imgAspect;
      }

      // Calculate image position on canvas
      const baseCenterX = (containerWidth - baseWidth) / 2;
      const baseCenterY = (containerHeight - baseHeight) / 2;
      const imgX = baseCenterX + panX;
      const imgY = baseCenterY + panY;
      const zoomedWidth = baseWidth * zoom;
      const zoomedHeight = baseHeight * zoom;

      // Get mouse position relative to canvas
      const canvasX = e.clientX - rect.left;
      const canvasY = e.clientY - rect.top;

      // Convert to normalized image coordinates (0-1)
      const normalizedX = (canvasX - imgX) / zoomedWidth;
      const normalizedY = (canvasY - imgY) / zoomedHeight;

      return { x: normalizedX, y: normalizedY };
    },
    [canvasRef, imageWidth, imageHeight, zoom, panX, panY]
  );

  const findAnnotationAtPoint = useCallback(
    (normalizedX: number, normalizedY: number): string | null => {
      // Search in reverse order so topmost (last drawn) is found first
      for (let i = annotations.length - 1; i >= 0; i--) {
        const annotation = annotations[i];
        if (pointInPolygon(normalizedX, normalizedY, annotation.polygon)) {
          return annotation.id;
        }
      }
      return null;
    },
    [annotations]
  );

  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      // Pan mode: start panning
      if (isSpaceHeld) {
        panStartRef.current = { x: e.clientX, y: e.clientY };
        onPanStart();
        return;
      }

      const coords = getCanvasCoordinates(e);
      if (!coords) return;

      // Detect Cmd/Ctrl modifier for multi-select
      const isModifierHeld = e.metaKey || e.ctrlKey;

      // Check if clicking on existing annotation
      const clickedId = findAnnotationAtPoint(coords.x, coords.y);
      if (clickedId) {
        onAnnotationClicked(clickedId, isModifierHeld);
        return;
      }

      // Start drawing new rectangle (clicking empty canvas also deselects)
      onAnnotationClicked(null, isModifierHeld);
      drawingStateRef.current = {
        isDrawing: true,
        startX: coords.x,
        startY: coords.y,
        currentRect: null,
      };
    },
    [getCanvasCoordinates, findAnnotationAtPoint, onAnnotationClicked, isSpaceHeld, onPanStart]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      // Pan mode: update pan offset
      if (panStartRef.current) {
        const deltaX = e.clientX - panStartRef.current.x;
        const deltaY = e.clientY - panStartRef.current.y;
        panStartRef.current = { x: e.clientX, y: e.clientY };
        onPan(deltaX, deltaY);
        return;
      }

      const coords = getCanvasCoordinates(e);

      // Track hover state even when not drawing
      if (coords && onAnnotationHovered) {
        const hoveredId = findAnnotationAtPoint(coords.x, coords.y);
        onAnnotationHovered(hoveredId);
      }

      if (!drawingStateRef.current.isDrawing) return;

      if (!coords) return;

      const { startX, startY } = drawingStateRef.current;
      const rect: Rectangle = {
        x: Math.min(startX, coords.x),
        y: Math.min(startY, coords.y),
        width: Math.abs(coords.x - startX),
        height: Math.abs(coords.y - startY),
      };

      drawingStateRef.current.currentRect = rect;
      setPreviewRect(rect);
    },
    [getCanvasCoordinates, onPan, onAnnotationHovered, findAnnotationAtPoint]
  );

  const handleMouseUp = useCallback(() => {
    // End panning
    if (panStartRef.current) {
      panStartRef.current = null;
      onPanEnd();
      return;
    }

    if (!drawingStateRef.current.isDrawing) return;

    const rect = drawingStateRef.current.currentRect;
    if (rect && rect.width > 0 && rect.height > 0) {
      onRectangleDrawn(rect);
    }

    drawingStateRef.current = {
      isDrawing: false,
      startX: 0,
      startY: 0,
      currentRect: null,
    };
    setPreviewRect(null);
  }, [onRectangleDrawn, onPanEnd]);

  const handleDoubleClick = useCallback(
    (e: MouseEvent) => {
      const coords = getCanvasCoordinates(e);
      if (!coords) return;

      // Only reset if not clicking on an annotation
      const clickedId = findAnnotationAtPoint(coords.x, coords.y);
      if (!clickedId) {
        onResetView();
      }
    },
    [getCanvasCoordinates, findAnnotationAtPoint, onResetView]
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseUp);
    canvas.addEventListener('dblclick', handleDoubleClick);

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('mouseleave', handleMouseUp);
      canvas.removeEventListener('dblclick', handleDoubleClick);
    };
  }, [canvasRef, handleMouseDown, handleMouseMove, handleMouseUp, handleDoubleClick]);

  return { previewRect };
}
