/**
 * Tests for MEI 5.0 reader/writer (frontend).
 *
 * Loads the same fixtures as the backend tests (spec/fixtures/) and
 * verifies semantic round-trip on the frontend side.
 */

import { readFileSync, readdirSync } from 'fs';
import { join, resolve } from 'path';
import { describe, expect, test } from 'vitest';

import { meiToAnnotations, annotationsToMEI } from './meiIO';

const FIXTURES_DIR = resolve(__dirname, '../../spec/fixtures');
const FIXTURES = readdirSync(FIXTURES_DIR).filter((f) => f.endsWith('.mei'));

function loadFixture(name: string): string {
  return readFileSync(join(FIXTURES_DIR, name), 'utf-8');
}

describe('meiToAnnotations: every fixture parses', () => {
  for (const fixture of FIXTURES) {
    test(fixture, () => {
      const data = meiToAnnotations(loadFixture(fixture));
      expect(data.imageDimensions.width).toBeGreaterThan(0);
      expect(data.imageDimensions.height).toBeGreaterThan(0);
      expect(data.imageFilename).toBe('image.jpg');
    });
  }
});

describe('semantic round-trip', () => {
  for (const fixture of FIXTURES) {
    test(`${fixture}: parse → write → parse preserves model`, () => {
      const a = meiToAnnotations(loadFixture(fixture));
      const written = annotationsToMEI(
        a.annotations,
        a.lineBoundaries,
        a.imageDimensions,
        a.imageFilename,
      );
      const b = meiToAnnotations(written);

      // Same number of annotations
      expect(b.annotations.length).toBe(a.annotations.length);
      // Same syllable texts (in some order; we compare sorted)
      const sylText = (data: typeof a) =>
        data.annotations
          .filter((x) => x.type === 'syllable')
          .map((x) => x.text || '')
          .sort();
      expect(sylText(b)).toEqual(sylText(a));
      // Same neume types
      const neumeTypes = (data: typeof a) =>
        data.annotations
          .filter((x) => x.type === 'neume')
          .map((x) => x.neumeType || '')
          .sort();
      expect(neumeTypes(b)).toEqual(neumeTypes(a));
      // Same number of line boundaries
      expect(b.lineBoundaries.length).toBe(a.lineBoundaries.length);
    });
  }
});

describe('per-fixture assertions', () => {
  test('01_simple_line: 1 syllable Te, 1 punctum', () => {
    const data = meiToAnnotations(loadFixture('01_simple_line.mei'));
    const sylls = data.annotations.filter((a) => a.type === 'syllable');
    const neumes = data.annotations.filter((a) => a.type === 'neume');
    expect(sylls.length).toBe(1);
    expect(sylls[0].text).toBe('Te');
    expect(neumes.length).toBe(1);
    expect(neumes[0].neumeType).toBe('punctum');
    expect(data.lineBoundaries.length).toBe(1);
    expect(data.lineBoundaries[0].syllableIds).toEqual([sylls[0].id]);
  });

  test('02_hyphenated_multi_line: hyphen reconstruction from wordpos', () => {
    const data = meiToAnnotations(loadFixture('02_hyphenated_multi_line.mei'));
    const sylls = data.annotations.filter((a) => a.type === 'syllable');
    const texts = sylls.map((s) => s.text);
    expect(texts).toContain('Do-');
    expect(texts).toContain('mi-');
    expect(texts).toContain('ne');
    expect(texts).toContain('san-');
    expect(texts).toContain('ctus');
    expect(data.lineBoundaries.length).toBe(2);
  });

  test('05_no_syllables: synthetic line dropped, neumes flat', () => {
    const data = meiToAnnotations(loadFixture('05_no_syllables.mei'));
    expect(data.lineBoundaries.length).toBe(0);
    const sylls = data.annotations.filter((a) => a.type === 'syllable');
    const neumes = data.annotations.filter((a) => a.type === 'neume');
    expect(sylls.length).toBe(0);
    expect(neumes.length).toBe(2);
  });

  test('06_polygonal_boundary: non-rect polygon preserved', () => {
    const data = meiToAnnotations(loadFixture('06_polygonal_boundary.mei'));
    const sylls = data.annotations.filter((a) => a.type === 'syllable');
    expect(sylls.length).toBe(3);
    const poly = sylls[0].polygon;
    expect(poly.length).toBe(4);
    // Check it's not a perfect axis-aligned rect: the y-coords shouldn't
    // collapse to just two values
    const ys = new Set(poly.map((p) => p[1]));
    const xs = new Set(poly.map((p) => p[0]));
    expect(ys.size + xs.size).toBeGreaterThan(4);
  });
});

describe('writer output is valid MEI', () => {
  test('writer produces parseable XML with correct namespace', () => {
    const data = meiToAnnotations(loadFixture('01_simple_line.mei'));
    const written = annotationsToMEI(
      data.annotations,
      data.lineBoundaries,
      data.imageDimensions,
      data.imageFilename,
    );
    expect(written.startsWith("<?xml version='1.0' encoding='UTF-8'?>\n")).toBe(true);
    expect(written).toContain('xmlns="http://www.music-encoding.org/ns/mei"');
    expect(written).toContain('meiversion="5.0"');
  });

  test('writer is deterministic', () => {
    const data = meiToAnnotations(loadFixture('02_hyphenated_multi_line.mei'));
    const a = annotationsToMEI(
      data.annotations,
      data.lineBoundaries,
      data.imageDimensions,
      data.imageFilename,
    );
    const b = annotationsToMEI(
      data.annotations,
      data.lineBoundaries,
      data.imageDimensions,
      data.imageFilename,
    );
    expect(a).toBe(b);
  });
});
