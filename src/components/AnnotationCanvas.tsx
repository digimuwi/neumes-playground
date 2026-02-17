import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { useAppContext } from '../state/context';
import { addAnnotation, addAnnotationWithPolygon, addAnnotations, selectAnnotation, selectAnnotations, toggleAnnotationSelection, updateAnnotation, clearNewFlag, deleteAnnotation, deleteAnnotations, setOcrDialog, setError, clearAnnotations, setLineBoundaries } from '../state/actions';
import { recognizeRegion, recognizePage } from '../services/htrService';
import { OcrDialog } from './dialogs/OcrDialog';
import { useCanvasDrawing } from '../hooks/useCanvasDrawing';
import { useNeumeAssignment } from '../hooks/useNeumeAssignment';
import { useTextLines, TextLine } from '../hooks/useTextLines';
import { useSuggestion } from '../hooks/useSuggestion';
import { useNeumeSuggestion } from '../hooks/useNeumeSuggestion';
import { drawAssignmentCurve } from '../hooks/useCurveDrawing';
import { Annotation, NeumeType, OcrProgressEvent, Rectangle } from '../state/types';
import { polygonBounds, polygonCenterX, polygonBottomY, polygonMinX, closestPointOnPolygon } from '../utils/polygonUtils';
import { InlineAnnotationEditor } from './InlineAnnotationEditor';
import { HelpButton } from './HelpButton';
import { detectMargins, computeOtsuThreshold, tightenRectangle, tightenToPolygon, OTSU_THRESHOLD_BIAS } from '../utils/imageProcessing';

const SYLLABLE_COLOR = 'rgba(66, 133, 244, 0.4)';
const SYLLABLE_BORDER = 'rgba(66, 133, 244, 1)';
const NEUME_COLOR = 'rgba(234, 67, 53, 0.4)';
const NEUME_BORDER = 'rgba(234, 67, 53, 1)';
const SELECTED_BORDER = 'rgba(251, 188, 5, 1)';
const PREVIEW_COLOR = 'rgba(52, 168, 83, 0.3)';
const PREVIEW_BORDER = 'rgba(52, 168, 83, 1)';
const TEXT_LINE_COLOR = 'rgba(147, 112, 219, 0.6)';
const TEXT_LINE_NUMBER_COLOR = 'rgba(147, 112, 219, 0.8)';

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 5;
const POPOVER_WIDTH = 280;
const POPOVER_HEIGHT = 100;
const POPOVER_GAP = 8;

const TYPE_PRIORITY: Array<'syllable' | 'neume'> = ['syllable', 'neume'];

function sortAnnotationsForCycling(annotations: Annotation[]): Annotation[] {
  return [...annotations].sort((a, b) => {
    // Primary sort: by type priority (syllables first, then neumes)
    const aTypePriority = TYPE_PRIORITY.indexOf(a.type);
    const bTypePriority = TYPE_PRIORITY.indexOf(b.type);
    const aPriority = aTypePriority === -1 ? TYPE_PRIORITY.length : aTypePriority;
    const bPriority = bTypePriority === -1 ? TYPE_PRIORITY.length : bTypePriority;
    if (aPriority !== bPriority) return aPriority - bPriority;

    // Secondary sort: by reading order (top-to-bottom, left-to-right)
    const aBounds = polygonBounds(a.polygon);
    const bBounds = polygonBounds(b.polygon);
    const aY = (aBounds.minY + aBounds.maxY) / 2;
    const bY = (bBounds.minY + bBounds.maxY) / 2;
    if (Math.abs(aY - bY) > 0.02) return aY - bY;
    return polygonCenterX(a.polygon) - polygonCenterX(b.polygon);
  });
}

const LINE_EXTENT_PADDING = 0.01;

function getLineExtent(line: TextLine): { xMin: number; xMax: number } {
  const syllables = line.syllables;
  if (syllables.length === 0) return { xMin: 0, xMax: 0 };

  let xMin = Infinity;
  let xMax = -Infinity;

  for (const s of syllables) {
    const bounds = polygonBounds(s.polygon);
    xMin = Math.min(xMin, bounds.minX);
    xMax = Math.max(xMax, bounds.maxX);
  }

  return {
    xMin: xMin - LINE_EXTENT_PADDING,
    xMax: xMax + LINE_EXTENT_PADDING,
  };
}

function drawTextLineBaseline(
  ctx: CanvasRenderingContext2D,
  line: TextLine,
  toScreenX: (x: number) => number,
  toScreenY: (y: number) => number
): { startX: number; startY: number } {
  const { xMin, xMax } = getLineExtent(line);
  const yAtXMin = line.slope * xMin + line.intercept;
  const yAtXMax = line.slope * xMax + line.intercept;

  const screenX1 = toScreenX(xMin);
  const screenY1 = toScreenY(yAtXMin);
  const screenX2 = toScreenX(xMax);
  const screenY2 = toScreenY(yAtXMax);

  ctx.strokeStyle = TEXT_LINE_COLOR;
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  ctx.moveTo(screenX1, screenY1);
  ctx.lineTo(screenX2, screenY2);
  ctx.stroke();
  ctx.setLineDash([]);

  return { startX: screenX1, startY: screenY1 };
}

const CIRCLED_NUMBERS = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳'];

function drawLineNumber(
  ctx: CanvasRenderingContext2D,
  lineIndex: number,
  startX: number,
  startY: number
): void {
  const number = lineIndex < CIRCLED_NUMBERS.length
    ? CIRCLED_NUMBERS[lineIndex]
    : `(${lineIndex + 1})`;

  ctx.font = '14px sans-serif';
  ctx.fillStyle = TEXT_LINE_NUMBER_COLOR;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'right';
  ctx.fillText(number, startX - 4, startY);
}

export function AnnotationCanvas() {
  const { state, dispatch, recognitionMode, setRecognitionMode } = useAppContext();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [isSpaceHeld, setIsSpaceHeld] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  const [hoveredAnnotationId, setHoveredAnnotationId] = useState<string | null>(null);
  const [marginThreshold, setMarginThreshold] = useState<number>(0);
  const [otsuThreshold, setOtsuThreshold] = useState<number | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const [loadingRegion, setLoadingRegion] = useState<Rectangle | null>(null);
  const [blinkPhase, setBlinkPhase] = useState(0);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Compute neume-to-syllable assignments
  const neumeAssignments = useNeumeAssignment(state.annotations);

  // Compute text lines for visualization
  const textLines = useTextLines(state.annotations);

  // Get the single selected annotation (for editor) - only when exactly one is selected
  const selectedAnnotation =
    state.selectedAnnotationIds.size === 1
      ? state.annotations.find((a) => state.selectedAnnotationIds.has(a.id))
      : undefined;

  // Get syllable suggestion from Cantus Index
  const suggestion = useSuggestion(
    state.annotations,
    selectedAnnotation || null,
    state.isNewlyCreated
  );

  // Get neume type suggestion from image classification
  const neumeSuggestion = useNeumeSuggestion(
    selectedAnnotation || null,
    state.isNewlyCreated,
    imageRef,
    otsuThreshold,
    marginThreshold
  );

  const sortedAnnotations = useMemo(
    () => sortAnnotationsForCycling(state.annotations),
    [state.annotations]
  );

  const calculatePopoverPosition = useCallback(() => {
    const container = containerRef.current;
    const img = imageRef.current;
    if (!container || !img || !selectedAnnotation) return null;

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;
    const imgAspect = img.width / img.height;
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

    const zoomedWidth = baseWidth * zoom;
    const zoomedHeight = baseHeight * zoom;
    const baseCenterX = (containerWidth - baseWidth) / 2;
    const baseCenterY = (containerHeight - baseHeight) / 2;
    const imgX = baseCenterX + panX;
    const imgY = baseCenterY + panY;

    const bounds = polygonBounds(selectedAnnotation.polygon);
    const rectRight = imgX + bounds.maxX * zoomedWidth;
    const rectLeft = imgX + bounds.minX * zoomedWidth;
    const rectTop = imgY + bounds.minY * zoomedHeight;

    let popoverX: number;
    if (rectRight + POPOVER_GAP + POPOVER_WIDTH <= containerWidth) {
      popoverX = rectRight + POPOVER_GAP;
    } else {
      popoverX = rectLeft - POPOVER_GAP - POPOVER_WIDTH;
    }

    let popoverY = rectTop;
    if (popoverY + POPOVER_HEIGHT > containerHeight) {
      popoverY = containerHeight - POPOVER_HEIGHT;
    }
    if (popoverY < 0) {
      popoverY = 0;
    }

    return { x: popoverX, y: popoverY };
  }, [selectedAnnotation, zoom, panX, panY]);

  const popoverPosition = calculatePopoverPosition();

  const handleClose = useCallback(() => {
    dispatch(selectAnnotation(null));
  }, [dispatch]);

  const handleTypeChange = useCallback(
    (type: 'syllable' | 'neume') => {
      if (!selectedAnnotation) return;
      dispatch(
        updateAnnotation(selectedAnnotation.id, {
          type,
          text: type === 'syllable' ? selectedAnnotation.text || '' : undefined,
          neumeType: type === 'neume' ? selectedAnnotation.neumeType || NeumeType.PUNCTUM : undefined,
        })
      );
    },
    [dispatch, selectedAnnotation]
  );

  const handleTextChange = useCallback(
    (text: string) => {
      if (!selectedAnnotation) return;
      dispatch(updateAnnotation(selectedAnnotation.id, { text }));
    },
    [dispatch, selectedAnnotation]
  );

  const handleNeumeTypeChange = useCallback(
    (neumeType: NeumeType) => {
      if (!selectedAnnotation) return;
      dispatch(updateAnnotation(selectedAnnotation.id, { neumeType }));
    },
    [dispatch, selectedAnnotation]
  );

  const handleClearNewFlag = useCallback(() => {
    dispatch(clearNewFlag());
  }, [dispatch]);

  const getImageBlob = useCallback(async (): Promise<Blob | null> => {
    const img = imageRef.current;
    if (!img) return null;

    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = img.width;
    offscreenCanvas.height = img.height;
    const offscreenCtx = offscreenCanvas.getContext('2d');
    if (!offscreenCtx) return null;

    offscreenCtx.drawImage(img, 0, 0);
    return new Promise<Blob | null>((resolve) =>
      offscreenCanvas.toBlob(resolve, 'image/jpeg', 0.95)
    );
  }, []);

  const handleProgress = useCallback(
    (event: OcrProgressEvent) => {
      if (event.stage === 'error') {
        dispatch(setOcrDialog({ mode: 'error', message: event.message }));
      } else if (event.stage === 'recognizing') {
        dispatch(setOcrDialog({ mode: 'loading', stage: 'recognizing', current: event.current, total: event.total }));
      } else {
        dispatch(setOcrDialog({ mode: 'loading', stage: event.stage }));
      }
    },
    [dispatch]
  );

  const handleFullPageOcr = useCallback(
    async (shouldClearFirst: boolean) => {
      const img = imageRef.current;
      if (!img) return;

      dispatch(setOcrDialog({ mode: 'loading', stage: 'loading' }));

      if (shouldClearFirst) {
        dispatch(clearAnnotations());
      }

      const blob = await getImageBlob();
      if (!blob) {
        dispatch(setOcrDialog({ mode: 'closed' }));
        dispatch(setError('Failed to process image'));
        return;
      }

      try {
        const result = await recognizePage(
          blob,
          { width: img.width, height: img.height },
          handleProgress
        );

        dispatch(setOcrDialog({ mode: 'closed' }));

        if (result.annotations.length > 0) {
          dispatch(addAnnotations(result.annotations));
          dispatch(setLineBoundaries(result.lineBoundaries));
        }
      } catch (error) {
        console.error('OCR recognition failed:', error);
        dispatch(setOcrDialog({ mode: 'error', message: 'OCR recognition failed. Is the backend running?' }));
      }
    },
    [dispatch, getImageBlob, handleProgress]
  );

  const handleCloseOcrDialog = useCallback(() => {
    dispatch(setOcrDialog({ mode: 'closed' }));
  }, [dispatch]);

  const handleAcceptUploadPrompt = useCallback(() => {
    handleFullPageOcr(false);
  }, [handleFullPageOcr]);

  const handleKeepAndAdd = useCallback(() => {
    handleFullPageOcr(false);
  }, [handleFullPageOcr]);

  const handleReplace = useCallback(() => {
    handleFullPageOcr(true);
  }, [handleFullPageOcr]);

  const handleTargetedRecognition = useCallback(
    async (rect: Rectangle, type: 'neume' | 'text') => {
      const img = imageRef.current;
      if (!img) return;

      setLoadingRegion(rect);

      const blob = await getImageBlob();
      if (!blob) {
        setLoadingRegion(null);
        dispatch(setError('Failed to process image'));
        return;
      }

      try {
        const result = await recognizeRegion(
          blob,
          rect,
          { width: img.width, height: img.height },
          undefined,
          type
        );

        setLoadingRegion(null);

        if (result.annotations.length > 0) {
          dispatch(addAnnotations(result.annotations));
          if (result.lineBoundaries.length > 0) {
            dispatch(setLineBoundaries([
              ...state.lineBoundaries,
              ...result.lineBoundaries,
            ]));
          }
        }
      } catch (error) {
        console.error('Targeted recognition failed:', error);
        setLoadingRegion(null);
        dispatch(setError('Recognition failed. Is the backend running?'));
      }
    },
    [dispatch, getImageBlob, state.lineBoundaries]
  );

  const handleRectangleDrawn = useCallback(
    (rect: Rectangle) => {
      // Recognition mode: send to backend with type parameter
      if (recognitionMode !== 'manual') {
        handleTargetedRecognition(rect, recognitionMode);
        return;
      }

      // Manual mode: inherit type from last annotation, default to syllable
      const lastAnnotation = state.annotations[state.annotations.length - 1];
      const annotationType = lastAnnotation?.type ?? 'syllable';

      const img = imageRef.current;
      if (img && otsuThreshold !== null) {
        const offscreenCanvas = document.createElement('canvas');
        offscreenCanvas.width = img.width;
        offscreenCanvas.height = img.height;
        const offscreenCtx = offscreenCanvas.getContext('2d');
        if (offscreenCtx) {
          offscreenCtx.drawImage(img, 0, 0);
          const imageData = offscreenCtx.getImageData(0, 0, img.width, img.height);

          if (annotationType === 'syllable') {
            // Syllables: tighten to contour polygon
            const polygon = tightenToPolygon(rect, imageData, otsuThreshold, marginThreshold, OTSU_THRESHOLD_BIAS);
            dispatch(addAnnotationWithPolygon(polygon, 'syllable'));
          } else {
            // Neumes: tighten to rectangle
            const finalRect = tightenRectangle(rect, imageData, otsuThreshold, marginThreshold, OTSU_THRESHOLD_BIAS);
            dispatch(addAnnotation(finalRect, annotationType));
          }
          return;
        }
      }

      // Fallback: no image or threshold — use rect as-is
      dispatch(addAnnotation(rect, annotationType));
    },
    [dispatch, state.annotations, otsuThreshold, marginThreshold, recognitionMode, handleTargetedRecognition]
  );

  const handleAnnotationClicked = useCallback(
    (id: string | null, isModifierHeld: boolean) => {
      if (id === null) {
        // Click on empty canvas - deselect all
        dispatch(selectAnnotation(null));
      } else if (isModifierHeld) {
        // Cmd/Ctrl+Click - toggle selection
        dispatch(toggleAnnotationSelection(id));
      } else {
        // Plain click - select only this one
        dispatch(selectAnnotation(id));
      }
    },
    [dispatch]
  );

  const handlePan = useCallback((deltaX: number, deltaY: number) => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img) return;

    // Calculate base dimensions
    const containerWidth = canvas.width;
    const containerHeight = canvas.height;
    const imgAspect = img.width / img.height;
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

    const zoomedWidth = baseWidth * zoom;
    const zoomedHeight = baseHeight * zoom;

    // Clamp pan to keep image partially visible
    const maxPanX = Math.max(0, (zoomedWidth - containerWidth) / 2 + containerWidth * 0.3);
    const maxPanY = Math.max(0, (zoomedHeight - containerHeight) / 2 + containerHeight * 0.3);

    setPanX((prev) => Math.max(-maxPanX, Math.min(maxPanX, prev + deltaX)));
    setPanY((prev) => Math.max(-maxPanY, Math.min(maxPanY, prev + deltaY)));
  }, [zoom]);

  const handlePanStart = useCallback(() => {
    setIsPanning(true);
  }, []);

  const handlePanEnd = useCallback(() => {
    setIsPanning(false);
  }, []);

  const handleResetView = useCallback(() => {
    setZoom(1);
    setPanX(0);
    setPanY(0);
  }, []);

  const handleAnnotationHovered = useCallback((id: string | null) => {
    setHoveredAnnotationId(id);
  }, []);

  const { previewRect } = useCanvasDrawing({
    canvasRef: canvasRef as React.RefObject<HTMLCanvasElement>,
    imageWidth: imageDimensions.width,
    imageHeight: imageDimensions.height,
    annotations: state.annotations,
    onRectangleDrawn: handleRectangleDrawn,
    onAnnotationClicked: handleAnnotationClicked,
    onAnnotationHovered: handleAnnotationHovered,
    zoom,
    panX,
    panY,
    isSpaceHeld,
    onPan: handlePan,
    onPanStart: handlePanStart,
    onPanEnd: handlePanEnd,
    onResetView: handleResetView,
  });

  // Handle Ctrl+wheel zoom
  const handleWheel = useCallback(
    (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();

      const canvas = canvasRef.current;
      const img = imageRef.current;
      if (!canvas || !img) return;

      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Calculate base dimensions for centering offset
      const containerWidth = canvas.width;
      const containerHeight = canvas.height;
      const imgAspect = img.width / img.height;
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

      const baseCenterX = (containerWidth - baseWidth) / 2;
      const baseCenterY = (containerHeight - baseHeight) / 2;

      // Mouse position relative to where centered image origin would be
      const relMouseX = mouseX - baseCenterX;
      const relMouseY = mouseY - baseCenterY;

      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      const newZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * zoomFactor));

      // Adjust pan to keep mouse position stationary (in the relative coordinate system)
      const newPanX = relMouseX - (relMouseX - panX) * (newZoom / zoom);
      const newPanY = relMouseY - (relMouseY - panY) * (newZoom / zoom);

      setZoom(newZoom);
      setPanX(newPanX);
      setPanY(newPanY);
    },
    [zoom, panX, panY]
  );

  // Attach wheel listener
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // Animate blinking for loading region
  useEffect(() => {
    if (!loadingRegion) return;
    let frame: number;
    const animate = () => {
      setBlinkPhase(Date.now());
      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [loadingRegion]);

  // Track Space key for pan mode, Tab navigation, Cmd+A, Escape, Delete
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

      if (e.code === 'Space' && !e.repeat) {
        // Only enable pan mode if not typing in a text input
        if (isInInput) return;
        e.preventDefault();
        setIsSpaceHeld(true);
      }

      // Cmd/Ctrl+A - select all annotations
      if (e.key === 'a' && (e.metaKey || e.ctrlKey) && state.annotations.length > 0) {
        if (isInInput) return;
        e.preventDefault();
        dispatch(selectAnnotations(state.annotations.map((a) => a.id)));
      }

      // Escape - clear recognition mode and deselect all
      if (e.key === 'Escape') {
        if (recognitionMode !== 'manual') {
          e.preventDefault();
          setRecognitionMode('manual');
        }
        if (state.selectedAnnotationIds.size > 0) {
          e.preventDefault();
          dispatch(selectAnnotation(null));
        }
      }

      // n - select neume recognition mode
      if (e.key === 'n' && !isInInput) {
        e.preventDefault();
        setRecognitionMode('neume');
      }

      // t - select text recognition mode
      if (e.key === 't' && !isInInput) {
        e.preventDefault();
        setRecognitionMode('text');
      }

      // m - select manual mode
      if (e.key === 'm' && !isInInput) {
        e.preventDefault();
        setRecognitionMode('manual');
      }

      // Tab navigation - clears multi-selection, selects next/prev
      if (e.key === 'Tab' && sortedAnnotations.length > 0) {
        if (isInInput) return;
        e.preventDefault();

        // Find current position based on first selected annotation (if any)
        let currentIndex = -1;
        if (state.selectedAnnotationIds.size > 0) {
          const firstSelectedId = Array.from(state.selectedAnnotationIds)[0];
          currentIndex = sortedAnnotations.findIndex((a) => a.id === firstSelectedId);
        }

        let nextIndex: number;
        if (e.shiftKey) {
          nextIndex = currentIndex <= 0 ? sortedAnnotations.length - 1 : currentIndex - 1;
        } else {
          nextIndex = currentIndex >= sortedAnnotations.length - 1 ? 0 : currentIndex + 1;
        }

        dispatch(selectAnnotation(sortedAnnotations[nextIndex].id));
      }

      // Delete/Backspace - delete all selected annotations
      if ((e.key === 'Delete' || e.key === 'Backspace') && state.selectedAnnotationIds.size > 0) {
        if (isInInput) return;
        e.preventDefault();
        dispatch(deleteAnnotations(Array.from(state.selectedAnnotationIds)));
      }

      // ? key - toggle help dialog
      if (e.key === '?' && !isInInput) {
        e.preventDefault();
        setHelpOpen((prev) => !prev);
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpaceHeld(false);
        setIsPanning(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [sortedAnnotations, state.selectedAnnotationIds, state.annotations, dispatch, recognitionMode, setRecognitionMode]);

  // Load image when dataUrl changes
  useEffect(() => {
    if (!state.imageDataUrl) {
      imageRef.current = null;
      setImageDimensions({ width: 0, height: 0 });
      setMarginThreshold(0);
      setOtsuThreshold(null);
      return;
    }

    const img = new Image();
    img.onload = () => {
      imageRef.current = img;
      setImageDimensions({ width: img.width, height: img.height });

      // Compute thresholds for bounding box tightening
      const offscreenCanvas = document.createElement('canvas');
      offscreenCanvas.width = img.width;
      offscreenCanvas.height = img.height;
      const offscreenCtx = offscreenCanvas.getContext('2d');
      if (offscreenCtx) {
        offscreenCtx.drawImage(img, 0, 0);
        const imageData = offscreenCtx.getImageData(0, 0, img.width, img.height);
        // Detect margins and compute Otsu threshold excluding margin pixels
        const detectedMarginThreshold = detectMargins(imageData);
        const threshold = computeOtsuThreshold(imageData, detectedMarginThreshold);
        setMarginThreshold(detectedMarginThreshold);
        setOtsuThreshold(threshold);
      }
    };
    img.src = state.imageDataUrl;
  }, [state.imageDataUrl]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const img = imageRef.current;
    if (!canvas || !container || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Canvas fills the container
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;
    canvas.width = containerWidth;
    canvas.height = containerHeight;

    // Calculate base image size (what it would be at zoom=1 to fit container)
    const imgAspect = img.width / img.height;
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

    // Clear canvas
    ctx.clearRect(0, 0, containerWidth, containerHeight);

    // Calculate zoomed image dimensions and position
    const zoomedWidth = baseWidth * zoom;
    const zoomedHeight = baseHeight * zoom;

    // Center the image when at zoom=1, pan=0
    const baseCenterX = (containerWidth - baseWidth) / 2;
    const baseCenterY = (containerHeight - baseHeight) / 2;

    // Apply pan offset to the centered position
    const imgX = baseCenterX + panX;
    const imgY = baseCenterY + panY;

    // Draw the zoomed image
    ctx.drawImage(img, imgX, imgY, zoomedWidth, zoomedHeight);

    // Helper to convert normalized coords to screen coords
    const toScreenX = (normX: number) => imgX + normX * zoomedWidth;
    const toScreenY = (normY: number) => imgY + normY * zoomedHeight;
    // Build lookup from syllable ID to line boundary confidence
    const syllableToConfidence = new Map<string, number>();
    for (const lb of state.lineBoundaries) {
      if (lb.confidence !== undefined) {
        for (const sid of lb.syllableIds) {
          syllableToConfidence.set(sid, lb.confidence);
        }
      }
    }

    // Draw text line baselines (before annotations, so they appear behind)
    textLines.forEach((line, index) => {
      if (line.syllables.length === 0) return;
      const { startX, startY } = drawTextLineBaseline(ctx, line, toScreenX, toScreenY);
      drawLineNumber(ctx, index, startX, startY);

      // Draw per-line OCR confidence at the end of the baseline
      const lineConfidence = line.syllables
        .map(s => syllableToConfidence.get(s.id))
        .find(c => c !== undefined);
      if (lineConfidence !== undefined) {
        const { xMax } = getLineExtent(line);
        const yAtXMax = line.slope * xMax + line.intercept;
        const endX = toScreenX(xMax);
        const endY = toScreenY(yAtXMax);

        const pct = Math.round(lineConfidence * 100);
        const color = lineConfidence >= 0.8
          ? 'rgba(52, 168, 83, 0.8)'
          : lineConfidence >= 0.5
            ? 'rgba(251, 188, 5, 0.8)'
            : 'rgba(234, 67, 53, 0.8)';

        ctx.font = '12px monospace';
        ctx.fillStyle = color;
        ctx.textBaseline = 'middle';
        ctx.textAlign = 'left';
        ctx.fillText(`${pct}%`, endX + 8, endY);
      }
    });

    // Draw annotations (polygon coordinates are normalized 0-1)
    for (const annotation of state.annotations) {
      const poly = annotation.polygon;
      if (poly.length < 2) continue;

      const isSelected = state.selectedAnnotationIds.has(annotation.id);
      const fillColor = annotation.type === 'syllable' ? SYLLABLE_COLOR : NEUME_COLOR;
      const borderColor = isSelected
        ? SELECTED_BORDER
        : annotation.type === 'syllable'
          ? SYLLABLE_BORDER
          : NEUME_BORDER;

      ctx.beginPath();
      ctx.moveTo(toScreenX(poly[0][0]), toScreenY(poly[0][1]));
      for (let i = 1; i < poly.length; i++) {
        ctx.lineTo(toScreenX(poly[i][0]), toScreenY(poly[i][1]));
      }
      ctx.closePath();

      ctx.fillStyle = fillColor;
      ctx.fill();

      ctx.strokeStyle = borderColor;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.stroke();
    }

    // Draw assignment curves (neume → syllable connections)
    const annotationsById = new Map(state.annotations.map((a) => [a.id, a]));
    for (const [neumeId, syllableId] of neumeAssignments) {
      const neume = annotationsById.get(neumeId);
      const syllable = annotationsById.get(syllableId);
      if (!neume || !syllable) continue;

      // Neume lower-left corner (minX, maxY of polygon)
      const neumeX = polygonMinX(neume.polygon);
      const neumeY = polygonBottomY(neume.polygon);

      // Closest point on syllable polygon
      const endpoint = closestPointOnPolygon(neumeX, neumeY, syllable.polygon);

      // Determine if this curve should be highlighted
      const isHighlighted =
        state.selectedAnnotationIds.has(neumeId) ||
        state.selectedAnnotationIds.has(syllableId) ||
        neumeId === hoveredAnnotationId ||
        syllableId === hoveredAnnotationId;

      drawAssignmentCurve(
        ctx,
        neumeX,
        neumeY,
        endpoint.x,
        endpoint.y,
        isHighlighted,
        toScreenX,
        toScreenY
      );
    }

    // Draw preview rectangle as polygon path
    if (previewRect) {
      const { x, y, width, height } = previewRect;

      ctx.beginPath();
      ctx.moveTo(toScreenX(x), toScreenY(y));
      ctx.lineTo(toScreenX(x + width), toScreenY(y));
      ctx.lineTo(toScreenX(x + width), toScreenY(y + height));
      ctx.lineTo(toScreenX(x), toScreenY(y + height));
      ctx.closePath();

      ctx.fillStyle = PREVIEW_COLOR;
      ctx.fill();

      ctx.strokeStyle = PREVIEW_BORDER;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Draw loading region with pulsing opacity
    if (loadingRegion) {
      const { x, y, width, height } = loadingRegion;
      const opacity = 0.15 + 0.2 * Math.sin(blinkPhase * 0.005);

      ctx.beginPath();
      ctx.moveTo(toScreenX(x), toScreenY(y));
      ctx.lineTo(toScreenX(x + width), toScreenY(y));
      ctx.lineTo(toScreenX(x + width), toScreenY(y + height));
      ctx.lineTo(toScreenX(x), toScreenY(y + height));
      ctx.closePath();

      ctx.fillStyle = `rgba(52, 168, 83, ${Math.max(0, opacity)})`;
      ctx.fill();

      ctx.strokeStyle = PREVIEW_BORDER;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [state.annotations, state.selectedAnnotationIds, state.lineBoundaries, imageDimensions, previewRect, zoom, panX, panY, neumeAssignments, hoveredAnnotationId, textLines, loadingRegion, blinkPhase]);

  const handleContainerClick = useCallback(
    (e: React.MouseEvent) => {
      // If clicking on the popover, don't close
      if (popoverRef.current?.contains(e.target as Node)) {
        return;
      }
      // Canvas clicks are handled by useCanvasDrawing (which selects annotations or deselects)
    },
    []
  );

  if (!state.imageDataUrl) {
    return (
      <>
        <Paper
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f5f5f5',
            minHeight: 400,
            position: 'relative',
          }}
        >
          <Typography variant="body1" color="text.secondary">
            Upload an image to start annotating
          </Typography>
          <HelpButton open={helpOpen} onOpenChange={setHelpOpen} />
        </Paper>
        <OcrDialog
          state={state.ocrDialogState}
          onClose={handleCloseOcrDialog}
          onAcceptUploadPrompt={handleAcceptUploadPrompt}
          onKeepAndAdd={handleKeepAndAdd}
          onReplace={handleReplace}
        />
      </>
    );
  }

  return (
    <Box
      ref={containerRef}
      onClick={handleContainerClick}
      sx={{
        flex: 1,
        position: 'relative',
        backgroundColor: '#e0e0e0',
        overflow: 'hidden',
        minHeight: 400,
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          cursor: isPanning ? 'grabbing' : isSpaceHeld ? 'grab' : 'crosshair',
          display: 'block',
          width: '100%',
          height: '100%',
        }}
      />
      {selectedAnnotation && popoverPosition && (
        <div ref={popoverRef}>
          <InlineAnnotationEditor
            annotation={selectedAnnotation}
            position={popoverPosition}
            isNewlyCreated={state.isNewlyCreated}
            suggestion={suggestion}
            neumeSuggestion={neumeSuggestion}
            onTypeChange={handleTypeChange}
            onTextChange={handleTextChange}
            onNeumeTypeChange={handleNeumeTypeChange}
            onClose={handleClose}
            onClearNewFlag={handleClearNewFlag}
            onDelete={() => dispatch(deleteAnnotation(selectedAnnotation.id))}
          />
        </div>
      )}
      <OcrDialog
        state={state.ocrDialogState}
        onClose={handleCloseOcrDialog}
        onAcceptUploadPrompt={handleAcceptUploadPrompt}
        onKeepAndAdd={handleKeepAndAdd}
        onReplace={handleReplace}
      />
      <HelpButton open={helpOpen} onOpenChange={setHelpOpen} />
    </Box>
  );
}
