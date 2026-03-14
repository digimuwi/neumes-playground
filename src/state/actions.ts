import { v4 as uuidv4 } from 'uuid';
import { Action, Annotation, AppState, DocumentMetadata, LineBoundary } from './types';
import { rectToPolygon } from '../utils/polygonUtils';

export function setImage(dataUrl: string): Action {
  return { type: 'SET_IMAGE', payload: dataUrl };
}

export function addAnnotation(
  rect: { x: number; y: number; width: number; height: number },
  annotationType: 'syllable' | 'neume' = 'syllable'
): Action {
  const annotation: Annotation = {
    id: uuidv4(),
    type: annotationType,
    polygon: rectToPolygon(rect),
    text: annotationType === 'syllable' ? '' : undefined,
    neumeType: undefined, // Start blank so suggestions can show as ghost text
  };
  return { type: 'ADD_ANNOTATION', payload: annotation };
}

export function addAnnotationWithPolygon(
  polygon: number[][],
  annotationType: 'syllable' | 'neume' = 'syllable'
): Action {
  const annotation: Annotation = {
    id: uuidv4(),
    type: annotationType,
    polygon,
    text: annotationType === 'syllable' ? '' : undefined,
    neumeType: undefined,
  };
  return { type: 'ADD_ANNOTATION', payload: annotation };
}

export function addAnnotations(annotations: Annotation[]): Action {
  return { type: 'ADD_ANNOTATIONS', payload: annotations };
}

export function updateAnnotation(id: string, updates: Partial<Annotation>): Action {
  return { type: 'UPDATE_ANNOTATION', payload: { id, updates } };
}

export function deleteAnnotation(id: string): Action {
  return { type: 'DELETE_ANNOTATION', payload: id };
}

export function deleteAnnotations(ids: string[]): Action {
  return { type: 'DELETE_ANNOTATIONS', payload: ids };
}

export function selectAnnotation(id: string | null): Action {
  return { type: 'SELECT_ANNOTATION', payload: id };
}

export function selectAnnotations(ids: string[]): Action {
  return { type: 'SELECT_ANNOTATIONS', payload: ids };
}

export function toggleAnnotationSelection(id: string): Action {
  return { type: 'TOGGLE_ANNOTATION_SELECTION', payload: id };
}

export function undo(): Action {
  return { type: 'UNDO' };
}

export function redo(): Action {
  return { type: 'REDO' };
}

export function loadState(state: AppState): Action {
  return { type: 'LOAD_STATE', payload: state };
}

export function clearNewFlag(): Action {
  return { type: 'CLEAR_NEW_FLAG' };
}

export function setOcrDialog(state: import('./types').OcrDialogState): Action {
  return { type: 'SET_OCR_DIALOG', payload: state };
}

export function setError(message: string | null): Action {
  return { type: 'SET_ERROR', payload: message };
}

export function clearAnnotations(): Action {
  return { type: 'CLEAR_ANNOTATIONS' };
}

export function setLineBoundaries(lineBoundaries: LineBoundary[]): Action {
  return { type: 'SET_LINE_BOUNDARIES', payload: lineBoundaries };
}

export function setContributionId(id: string | null): Action {
  return { type: 'SET_CONTRIBUTION_ID', payload: id };
}

export function setMetadata(metadata: DocumentMetadata): Action {
  return { type: 'SET_METADATA', payload: metadata };
}
