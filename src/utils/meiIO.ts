/**
 * MEI 5.0 reader/writer for contribution annotations.
 *
 * See spec/mei-profile.md for the format definition. This module is the
 * only place in the frontend that knows about MEI XML; htrService.ts and
 * meiExport.ts consume the in-memory Annotation[] + LineBoundary[] models.
 */

import { v4 as uuidv4 } from 'uuid';
import { Annotation, LineBoundary } from '../state/types';
import {
  denormalizePolygon,
  normalizePolygon,
  polygonBounds,
  polygonCenterX,
} from './polygonUtils';
import { computeTextLines } from '../hooks/useTextLines';
import { computeNeumeAssignments } from '../hooks/useNeumeAssignment';

const MEI_NS = 'http://www.music-encoding.org/ns/mei';

export interface ImageDimensions {
  width: number;
  height: number;
}

export interface ContributionMEIData {
  annotations: Annotation[];
  lineBoundaries: LineBoundary[];
  imageDimensions: ImageDimensions;
  imageFilename: string;
}

// ---------------------------------------------------------------------------
// Reader
// ---------------------------------------------------------------------------

export function meiToAnnotations(xml: string): ContributionMEIData {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xml, 'application/xml');

  const parserError = doc.querySelector('parsererror');
  if (parserError) {
    throw new Error(`MEI parse error: ${parserError.textContent}`);
  }

  const surface = qs(doc, 'surface');
  if (!surface) {
    throw new Error('MEI document missing <surface>');
  }

  const imageDimensions: ImageDimensions = {
    width: parseInt(surface.getAttribute('lrx') || '0', 10),
    height: parseInt(surface.getAttribute('lry') || '0', 10),
  };
  if (!imageDimensions.width || !imageDimensions.height) {
    throw new Error('MEI <surface> missing valid lrx/lry');
  }

  const graphic = qs(surface, 'graphic');
  const imageFilename = graphic?.getAttribute('target') || 'image.jpg';

  const zones = readZones(surface);

  const layer = qs(doc, 'layer');
  if (!layer) {
    return {
      annotations: [],
      lineBoundaries: [],
      imageDimensions,
      imageFilename,
    };
  }

  const runs = splitLayerIntoLineRuns(layer);
  const annotations: Annotation[] = [];
  const lineBoundaries: LineBoundary[] = [];

  for (const { lineZoneId, syllableElements } of runs) {
    const linePolygonPx = zones.get(lineZoneId);
    if (!linePolygonPx) continue;

    // All-orphan synthetic line — drop the line, lift orphans flat
    const allOrphan =
      syllableElements.length > 0 &&
      syllableElements.every((syl) => isOrphanCarrier(syl, lineZoneId));

    if (allOrphan) {
      for (const syl of syllableElements) {
        for (const neumeEl of childrenByName(syl, 'neume')) {
          annotations.push(readNeume(neumeEl, zones, imageDimensions));
        }
      }
      continue;
    }

    const lineSyllableIds: string[] = [];
    for (const syl of syllableElements) {
      if (isOrphanCarrier(syl, lineZoneId)) {
        for (const neumeEl of childrenByName(syl, 'neume')) {
          annotations.push(readNeume(neumeEl, zones, imageDimensions));
        }
      } else {
        const sylAnnotation = readSyllable(syl, zones, imageDimensions);
        annotations.push(sylAnnotation);
        lineSyllableIds.push(sylAnnotation.id);
        for (const neumeEl of childrenByName(syl, 'neume')) {
          annotations.push(readNeume(neumeEl, zones, imageDimensions));
        }
      }
    }

    lineBoundaries.push({
      boundary: normalizePolygon(linePolygonPx, imageDimensions),
      syllableIds: lineSyllableIds,
    });
  }

  return {
    annotations,
    lineBoundaries,
    imageDimensions,
    imageFilename,
  };
}

function readZones(surface: Element): Map<string, number[][]> {
  const zones = new Map<string, number[][]>();
  for (const zone of childrenByName(surface, 'zone')) {
    const id = zone.getAttributeNS('http://www.w3.org/XML/1998/namespace', 'id');
    if (!id) continue;
    const points = zone.getAttribute('points');
    if (points) {
      zones.set(id, parsePoints(points));
    } else {
      const ulx = parseInt(zone.getAttribute('ulx') || '0', 10);
      const uly = parseInt(zone.getAttribute('uly') || '0', 10);
      const lrx = parseInt(zone.getAttribute('lrx') || '0', 10);
      const lry = parseInt(zone.getAttribute('lry') || '0', 10);
      zones.set(id, [
        [ulx, uly],
        [lrx, uly],
        [lrx, lry],
        [ulx, lry],
      ]);
    }
  }
  return zones;
}

function parsePoints(points: string): number[][] {
  return points
    .trim()
    .split(/\s+/)
    .map((token) => {
      const [x, y] = token.split(',').map((n) => parseInt(n, 10));
      return [x, y];
    });
}

interface LineRun {
  lineZoneId: string;
  syllableElements: Element[];
}

function splitLayerIntoLineRuns(layer: Element): LineRun[] {
  const runs: LineRun[] = [];
  let currentZoneId: string | null = null;
  let currentSyllables: Element[] = [];

  for (const child of Array.from(layer.children)) {
    const tag = localName(child);
    if (tag === 'lb') {
      if (currentZoneId !== null) {
        runs.push({
          lineZoneId: currentZoneId,
          syllableElements: currentSyllables,
        });
      }
      const facs = (child.getAttribute('facs') || '').replace(/^#/, '');
      currentZoneId = facs || null;
      currentSyllables = [];
    } else if (tag === 'syllable') {
      currentSyllables.push(child);
    }
  }

  if (currentZoneId !== null) {
    runs.push({
      lineZoneId: currentZoneId,
      syllableElements: currentSyllables,
    });
  }

  return runs;
}

function isOrphanCarrier(syl: Element, lineZoneId: string): boolean {
  const sylTextEl = qs(syl, 'syl');
  const hasText = !!(sylTextEl && (sylTextEl.textContent || '').trim() !== '');
  if (hasText) return false;
  const facs = (syl.getAttribute('facs') || '').replace(/^#/, '');
  return facs === lineZoneId;
}

function readSyllable(
  sylEl: Element,
  zones: Map<string, number[][]>,
  dimensions: ImageDimensions,
): Annotation {
  const facs = (sylEl.getAttribute('facs') || '').replace(/^#/, '');
  const polygonPx = zones.get(facs) || [];

  const sylTextEl = qs(sylEl, 'syl');
  const rawText = sylTextEl?.textContent || '';
  const wordpos = sylTextEl?.getAttribute('wordpos') || '';

  let text = rawText;
  if ((wordpos === 'i' || wordpos === 'm') && text !== '' && !text.endsWith('-')) {
    text = text + '-';
  }

  return {
    id: uuidv4(),
    type: 'syllable',
    polygon: normalizePolygon(polygonPx, dimensions),
    text,
  };
}

function readNeume(
  neumeEl: Element,
  zones: Map<string, number[][]>,
  dimensions: ImageDimensions,
): Annotation {
  const facs = (neumeEl.getAttribute('facs') || '').replace(/^#/, '');
  const polygonPx = zones.get(facs) || [];
  return {
    id: uuidv4(),
    type: 'neume',
    polygon: normalizePolygon(polygonPx, dimensions),
    neumeType: neumeEl.getAttribute('type') || 'unknown',
  };
}

function qs(root: Document | Element, tag: string): Element | null {
  return root.getElementsByTagNameNS(MEI_NS, tag).item(0);
}

function childrenByName(el: Element, tag: string): Element[] {
  return Array.from(el.children).filter((c) => localName(c) === tag);
}

function localName(el: Element): string {
  return el.localName || (el.tagName.includes(':') ? el.tagName.split(':').pop()! : el.tagName);
}

// ---------------------------------------------------------------------------
// Writer
// ---------------------------------------------------------------------------

export function annotationsToMEI(
  annotations: Annotation[],
  lineBoundaries: LineBoundary[],
  imageDimensions: ImageDimensions,
  imageFilename: string = 'image.jpg',
): string {
  // Group syllables into text lines, derive neume → syllable assignments
  const textLines = computeTextLines(annotations);
  const assignments = computeNeumeAssignments(annotations, textLines);

  const allNeumes = annotations.filter((a) => a.type === 'neume');

  // Build per-line ordering: each text line's syllables sorted left-to-right
  const linesInOrder = textLines.map((line) => ({
    syllables: [...line.syllables].sort(
      (a, b) => polygonCenterX(a.polygon) - polygonCenterX(b.polygon),
    ),
  }));

  // Build per-syllable neume bucket; any unassigned neumes become global
  // orphans (only happens when there are no syllables on any line)
  const sylNeumeMap = new Map<string, Annotation[]>();
  const globalOrphans: Annotation[] = [];

  for (const neume of allNeumes) {
    const owningSylId = assignments.get(neume.id);
    if (owningSylId !== undefined) {
      const arr = sylNeumeMap.get(owningSylId) || [];
      arr.push(neume);
      sylNeumeMap.set(owningSylId, arr);
    } else {
      globalOrphans.push(neume);
    }
  }

  // Sort neumes within each bucket by polygonCenterX
  for (const arr of sylNeumeMap.values()) {
    arr.sort((a, b) => polygonCenterX(a.polygon) - polygonCenterX(b.polygon));
  }
  globalOrphans.sort((a, b) => polygonCenterX(a.polygon) - polygonCenterX(b.polygon));

  // Find a stored line boundary (in pixel coords) for each text line:
  // match via any syllable id that the LineBoundary lists
  const lineBoundaryFor = (lineIdx: number): number[][] | null => {
    const sylIds = new Set(linesInOrder[lineIdx].syllables.map((s) => s.id));
    for (const lb of lineBoundaries) {
      if (lb.syllableIds.some((id) => sylIds.has(id))) {
        return denormalizePolygon(lb.boundary, imageDimensions);
      }
    }
    // Fallback: bounding box of the syllables in this line
    if (linesInOrder[lineIdx].syllables.length === 0) return null;
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const syl of linesInOrder[lineIdx].syllables) {
      const px = denormalizePolygon(syl.polygon, imageDimensions);
      const b = polygonBounds(px);
      if (b.minX < minX) minX = b.minX;
      if (b.minY < minY) minY = b.minY;
      if (b.maxX > maxX) maxX = b.maxX;
      if (b.maxY > maxY) maxY = b.maxY;
    }
    return [
      [Math.round(minX), Math.round(minY)],
      [Math.round(maxX), Math.round(minY)],
      [Math.round(maxX), Math.round(maxY)],
      [Math.round(minX), Math.round(maxY)],
    ];
  };

  // Detect synthetic global line: orphans exist AND no real lines
  const hasSyntheticLine = globalOrphans.length > 0 && linesInOrder.length === 0;

  // ----- Build XML -----
  const out: string[] = [];
  out.push("<?xml version='1.0' encoding='UTF-8'?>");
  out.push(
    `<mei meiversion="5.0" xmlns="${MEI_NS}">`,
  );
  out.push('  <meiHead>');
  out.push('    <fileDesc>');
  out.push('      <titleStmt>');
  out.push('        <title>Neumes Playground contribution</title>');
  out.push('      </titleStmt>');
  out.push('      <pubStmt/>');
  out.push('    </fileDesc>');
  out.push('  </meiHead>');
  out.push('  <music>');
  out.push('    <facsimile>');
  out.push(
    `      <surface lrx="${imageDimensions.width}" lry="${imageDimensions.height}" ulx="0" uly="0" xml:id="surface-1">`,
  );
  out.push(
    `        <graphic height="${imageDimensions.height}px" target="${escapeAttr(imageFilename)}" width="${imageDimensions.width}px"/>`,
  );

  // Stable xml:ids embedding the Annotation UUIDs (truncated to fit a single segment)
  const sylIdFor = (a: Annotation) => `syl-${a.id}`;
  const sylZoneIdFor = (a: Annotation) => `zone-syl-${a.id}`;
  const neumeIdFor = (a: Annotation) => `n-${a.id}`;
  const neumeZoneIdFor = (a: Annotation) => `zone-n-${a.id}`;

  // Emit zones — line zones first, then syllable zones, then neume zones
  const lineZoneIds: string[] = [];
  for (let i = 0; i < linesInOrder.length; i++) {
    const polygonPx = lineBoundaryFor(i);
    if (polygonPx) {
      const zid = `zone-line-${i + 1}`;
      lineZoneIds.push(zid);
      out.push('        ' + zoneTag(zid, polygonPx));
    } else {
      lineZoneIds.push('');
    }
  }
  if (hasSyntheticLine) {
    const syntheticPolygon = [
      [0, 0],
      [imageDimensions.width, 0],
      [imageDimensions.width, imageDimensions.height],
      [0, imageDimensions.height],
    ];
    out.push('        ' + zoneTag('zone-line-1', syntheticPolygon));
  }

  for (const line of linesInOrder) {
    for (const syl of line.syllables) {
      const polygonPx = denormalizePolygon(syl.polygon, imageDimensions);
      out.push('        ' + zoneTag(sylZoneIdFor(syl), polygonPx));
    }
  }

  for (const neume of allNeumes) {
    const polygonPx = denormalizePolygon(neume.polygon, imageDimensions);
    out.push('        ' + zoneTag(neumeZoneIdFor(neume), polygonPx));
  }

  out.push('      </surface>');
  out.push('    </facsimile>');
  out.push('    <body>');
  out.push('      <mdiv>');
  out.push('        <score>');
  out.push('          <section>');
  out.push('            <staff>');
  out.push('              <layer>');

  if (linesInOrder.length > 0) {
    for (let i = 0; i < linesInOrder.length; i++) {
      const lineN = i + 1;
      const lineZoneId = lineZoneIds[i] || `zone-line-${lineN}`;
      out.push(`                <lb facs="#${lineZoneId}" n="${lineN}"/>`);

      const wordposChain = computeWordpos(linesInOrder[i].syllables);
      for (let s = 0; s < linesInOrder[i].syllables.length; s++) {
        const syl = linesInOrder[i].syllables[s];
        const sylNeumes = sylNeumeMap.get(syl.id) || [];
        emitSyllable(out, syl, sylIdFor(syl), sylZoneIdFor(syl), wordposChain[s], sylNeumes, neumeIdFor, neumeZoneIdFor);
      }
    }
  } else if (hasSyntheticLine) {
    out.push('                <lb facs="#zone-line-1" n="1"/>');
    emitOrphanCarrier(out, 'zone-line-1', 1, globalOrphans, neumeIdFor, neumeZoneIdFor);
  }

  out.push('              </layer>');
  out.push('            </staff>');
  out.push('          </section>');
  out.push('        </score>');
  out.push('      </mdiv>');
  out.push('    </body>');
  out.push('  </music>');
  out.push('</mei>');
  return out.join('\n') + '\n';
}

function zoneTag(zoneId: string, polygon: number[][]): string {
  const xs = polygon.map((p) => p[0]);
  const ys = polygon.map((p) => p[1]);
  const ulx = Math.min(...xs);
  const uly = Math.min(...ys);
  const lrx = Math.max(...xs);
  const lry = Math.max(...ys);
  const points = polygon.map(([x, y]) => `${Math.round(x)},${Math.round(y)}`).join(' ');
  return `<zone lrx="${lrx}" lry="${lry}" points="${points}" ulx="${ulx}" uly="${uly}" xml:id="${escapeAttr(zoneId)}"/>`;
}

function emitSyllable(
  out: string[],
  syl: Annotation,
  sylId: string,
  sylZoneId: string,
  wordpos: string,
  sylNeumes: Annotation[],
  neumeIdFor: (n: Annotation) => string,
  neumeZoneIdFor: (n: Annotation) => string,
): void {
  out.push(
    `                <syllable facs="#${sylZoneId}" xml:id="${escapeAttr(sylId)}">`,
  );
  const text = syl.text || '';
  if (text === '') {
    out.push('                  <syl/>');
  } else {
    const stripped = text.endsWith('-') ? text.slice(0, -1) : text;
    const wordposAttr = wordpos ? ` wordpos="${wordpos}"` : '';
    out.push(`                  <syl${wordposAttr}>${escapeText(stripped)}</syl>`);
  }
  for (const neume of sylNeumes) {
    out.push(
      `                  <neume facs="#${neumeZoneIdFor(neume)}" type="${escapeAttr(neume.neumeType || 'punctum')}" xml:id="${escapeAttr(neumeIdFor(neume))}"/>`,
    );
  }
  out.push('                </syllable>');
}

function emitOrphanCarrier(
  out: string[],
  lineZoneId: string,
  lineN: number,
  neumes: Annotation[],
  neumeIdFor: (n: Annotation) => string,
  neumeZoneIdFor: (n: Annotation) => string,
): void {
  out.push(
    `                <syllable facs="#${lineZoneId}" xml:id="syl-orphan-${lineN}">`,
  );
  out.push('                  <syl/>');
  for (const neume of neumes) {
    out.push(
      `                  <neume facs="#${neumeZoneIdFor(neume)}" type="${escapeAttr(neume.neumeType || 'punctum')}" xml:id="${escapeAttr(neumeIdFor(neume))}"/>`,
    );
  }
  out.push('                </syllable>');
}

function computeWordpos(syllables: Annotation[]): string[] {
  const result: string[] = new Array(syllables.length).fill('');
  let prevEndedWithHyphen = false;
  for (let i = 0; i < syllables.length; i++) {
    const text = syllables[i].text || '';
    if (text === '') continue;
    const endsWithHyphen = text.endsWith('-');
    if (prevEndedWithHyphen) {
      result[i] = endsWithHyphen ? 'm' : 't';
    } else {
      result[i] = endsWithHyphen ? 'i' : 's';
    }
    prevEndedWithHyphen = endsWithHyphen;
  }
  return result;
}

function escapeAttr(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeText(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
