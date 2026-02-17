import { Annotation, DocumentMetadata } from '../state/types';

export interface AnnotationsFile {
  imageDataUrl: string;
  annotations: Annotation[];
  metadata?: DocumentMetadata;
}

export function exportAnnotationsJSON(
  imageDataUrl: string,
  annotations: Annotation[],
  metadata?: DocumentMetadata
): void {
  const data: AnnotationsFile = { imageDataUrl, annotations, metadata };
  const json = JSON.stringify(data);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'annotations.json';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
