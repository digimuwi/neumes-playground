import { AnnotationsFile } from './jsonExport';

export function parseAnnotationsJSON(file: File): Promise<AnnotationsFile> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const data = JSON.parse(text);

        if (typeof data.imageDataUrl !== 'string' || !Array.isArray(data.annotations)) {
          throw new Error('Invalid file: missing imageDataUrl or annotations');
        }

        resolve(data as AnnotationsFile);
      } catch (e) {
        reject(e instanceof Error ? e : new Error('Failed to parse JSON file'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}
