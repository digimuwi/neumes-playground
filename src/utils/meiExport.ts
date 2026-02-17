import { Annotation, DocumentMetadata } from '../state/types';
import { computeTextLines, TextLine } from '../hooks/useTextLines';
import { computeNeumeAssignments } from '../hooks/useNeumeAssignment';
import { polygonBounds, polygonCenterX } from '../utils/polygonUtils';

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
 * Converts a polygon's bounding rect from normalized (0-1) to pixel coordinates.
 */
export function denormalizePolygonBounds(
  polygon: number[][],
  dimensions: ImageDimensions
): { ulx: number; uly: number; lrx: number; lry: number } {
  const bounds = polygonBounds(polygon);
  const ulx = Math.round(bounds.minX * dimensions.width);
  const uly = Math.round(bounds.minY * dimensions.height);
  const lrx = Math.round(bounds.maxX * dimensions.width);
  const lry = Math.round(bounds.maxY * dimensions.height);
  return { ulx, uly, lrx, lry };
}

/**
 * Generates zone XML elements for all annotations.
 */
export function generateZones(
  annotations: Annotation[],
  dimensions: ImageDimensions
): string {
  return annotations
    .map((ann) => {
      const { ulx, uly, lrx, lry } = denormalizePolygonBounds(ann.polygon, dimensions);
      const zoneId =
        ann.type === 'syllable' ? `zone-syl-${ann.id}` : `zone-n-${ann.id}`;
      return `        <zone xml:id="${zoneId}" ulx="${ulx}" uly="${uly}" lrx="${lrx}" lry="${lry}"/>`;
    })
    .join('\n');
}

/**
 * Returns syllables sorted in reading order (by text line, then left-to-right within each line).
 */
export function getSyllablesInReadingOrder(textLines: TextLine[]): Annotation[] {
  const result: Annotation[] = [];

  for (const line of textLines) {
    // Sort syllables within the line by x position (left to right)
    const sortedSyllables = [...line.syllables].sort((a, b) => {
      return polygonCenterX(a.polygon) - polygonCenterX(b.polygon);
    });
    result.push(...sortedSyllables);
  }

  return result;
}

/**
 * Groups neumes by their assigned syllable, sorted left-to-right within each group.
 */
export function groupNeumesBySyllable(
  annotations: Annotation[],
  assignments: Map<string, string>
): Map<string, Annotation[]> {
  const neumes = annotations.filter((a) => a.type === 'neume');
  const grouped = new Map<string, Annotation[]>();

  for (const neume of neumes) {
    const syllableId = assignments.get(neume.id);
    if (!syllableId) {
      console.warn(`Orphan neume (no assigned syllable): ${neume.id}`);
      continue;
    }

    if (!grouped.has(syllableId)) {
      grouped.set(syllableId, []);
    }
    grouped.get(syllableId)!.push(neume);
  }

  // Sort neumes within each group by x position
  for (const [, neumeList] of grouped) {
    neumeList.sort((a, b) => {
      return polygonCenterX(a.polygon) - polygonCenterX(b.polygon);
    });
  }

  return grouped;
}

export type Wordpos = 'i' | 'm' | 't' | 's';

/**
 * Removes trailing hyphen from syllable text for MEI output.
 */
export function stripHyphen(text: string): string {
  return text.endsWith('-') ? text.slice(0, -1) : text;
}

/**
 * Computes wordpos for each syllable based on trailing hyphen convention.
 * - "i" (initial): first syllable of multi-syllable word
 * - "m" (middle): interior syllable of multi-syllable word
 * - "t" (terminal): last syllable of multi-syllable word
 * - "s" (single): complete word in one syllable
 * Empty syllables are skipped but don't break word chains.
 */
export function computeWordpos(syllables: Annotation[]): Map<string, Wordpos> {
  const result = new Map<string, Wordpos>();
  let prevNonEmptyEndedWithHyphen = false;

  for (const syllable of syllables) {
    const text = syllable.text || '';
    if (text === '') {
      // Empty syllables skip wordpos, don't update tracker
      continue;
    }

    const endsWithHyphen = text.endsWith('-');

    if (prevNonEmptyEndedWithHyphen) {
      result.set(syllable.id, endsWithHyphen ? 'm' : 't');
    } else {
      result.set(syllable.id, endsWithHyphen ? 'i' : 's');
    }

    prevNonEmptyEndedWithHyphen = endsWithHyphen;
  }

  return result;
}

/**
 * Escapes special XML characters in text content.
 */
function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * Generates XML for a single syllable element with its nested neumes.
 */
export function generateSyllableXML(
  syllable: Annotation,
  neumes: Annotation[],
  wordpos?: Wordpos
): string {
  const syllableId = `syl-${syllable.id}`;
  const facs = `#zone-syl-${syllable.id}`;
  const rawText = syllable.text || '';
  const sylText = rawText ? escapeXml(stripHyphen(rawText)) : '';

  const neumeElements = neumes
    .map((neume) => {
      const neumeId = `n-${neume.id}`;
      const neumeFacs = `#zone-n-${neume.id}`;
      const neumeType = neume.neumeType || 'punctum';
      return `            <neume xml:id="${neumeId}" type="${neumeType}" facs="${neumeFacs}"/>`;
    })
    .join('\n');

  const wordposAttr = wordpos ? ` wordpos="${wordpos}"` : '';

  if (sylText) {
    return `          <syllable xml:id="${syllableId}" facs="${facs}">
            <syl${wordposAttr}>${sylText}</syl>
${neumeElements}
          </syllable>`;
  } else {
    return `          <syllable xml:id="${syllableId}" facs="${facs}">
            <syl/>
${neumeElements}
          </syllable>`;
  }
}

/**
 * Generates the workList XML section when Cantus metadata is present.
 */
function generateWorkList(metadata?: DocumentMetadata): string {
  if (!metadata?.cantusId) {
    return '';
  }

  const genreElement = metadata.genre
    ? `
      <classification>
        <term type="genre">${metadata.genre}</term>
      </classification>`
    : '';

  return `
  <workList>
    <work>
      <identifier type="cantus">${metadata.cantusId}</identifier>${genreElement}
    </work>
  </workList>`;
}

/**
 * Generates the complete MEI XML document.
 */
export function generateMEI(
  annotations: Annotation[],
  dimensions: ImageDimensions,
  metadata?: DocumentMetadata
): string {
  const textLines = computeTextLines(annotations);
  const assignments = computeNeumeAssignments(annotations, textLines);

  const zones = generateZones(annotations, dimensions);
  const syllablesInOrder = getSyllablesInReadingOrder(textLines);
  const neumesBySyllable = groupNeumesBySyllable(annotations, assignments);
  const wordposMap = computeWordpos(syllablesInOrder);

  // Build layer content with <lb/> elements marking line beginnings
  const layerElements: string[] = [];
  let lineNumber = 1;

  for (const line of textLines) {
    // Skip empty lines
    if (line.syllables.length === 0) {
      continue;
    }

    // Emit line beginning marker
    layerElements.push(`          <lb n="${lineNumber}"/>`);
    lineNumber++;

    // Sort syllables within the line by x position (left to right)
    const sortedSyllables = [...line.syllables].sort((a, b) => {
      return polygonCenterX(a.polygon) - polygonCenterX(b.polygon);
    });

    // Emit syllable elements for this line
    for (const syllable of sortedSyllables) {
      const neumes = neumesBySyllable.get(syllable.id) || [];
      const wordpos = wordposMap.get(syllable.id);
      layerElements.push(generateSyllableXML(syllable, neumes, wordpos));
    }
  }

  const layerContent = layerElements.join('\n');
  const workList = generateWorkList(metadata);

  return `<?xml version="1.0" encoding="UTF-8"?>
<mei xmlns="http://www.music-encoding.org/ns/mei">
  <meiHead>
    <fileDesc>
      <titleStmt>
        <title>Exported from Neumes Playground</title>
      </titleStmt>
      <pubStmt/>
    </fileDesc>${workList}
  </meiHead>
  <music>
    <facsimile>
      <surface xml:id="surface-1" ulx="0" uly="0" lrx="${dimensions.width}" lry="${dimensions.height}">
        <graphic target="source-image.jpg" width="${dimensions.width}px" height="${dimensions.height}px"/>
${zones}
      </surface>
    </facsimile>
    <body>
      <mdiv>
        <score>
          <section>
            <staff>
              <layer>
${layerContent}
              </layer>
            </staff>
          </section>
        </score>
      </mdiv>
    </body>
  </music>
</mei>`;
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
  metadata?: DocumentMetadata
): Promise<void> {
  const dimensions = await getImageDimensions(imageDataUrl);
  const xml = generateMEI(annotations, dimensions, metadata);
  downloadMEI(xml, 'export.mei');
}
