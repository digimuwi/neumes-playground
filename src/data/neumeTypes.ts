import { NeumeClass } from '../state/types';

export const fallbackNeumeClasses: NeumeClass[] = [
  { id: 0, key: 'punctum', name: 'Punctum', description: 'Single note (dot)', active: true },
  { id: 1, key: 'clivis', name: 'Clivis', description: 'Two notes descending', active: true },
  { id: 2, key: 'podatus', name: 'Podatus', description: 'Two notes ascending', active: true },
  { id: 3, key: 'torculus', name: 'Torculus', description: 'Three notes: low-high-low', active: true },
  { id: 4, key: 'scandicus', name: 'Scandicus', description: 'Three notes ascending', active: true },
  { id: 5, key: 'climacus', name: 'Climacus', description: 'Three+ notes descending', active: true },
  { id: 6, key: 'porrectus', name: 'Porrectus', description: 'Three notes: high-low-high', active: true },
  { id: 7, key: 'pes', name: 'Pes', description: 'Two notes ascending', active: true },
  { id: 8, key: 'virga', name: 'Virga', description: 'Single note with stem', active: true },
  { id: 9, key: 'oriscus', name: 'Oriscus', description: 'Ornamental wavy note', active: true },
  { id: 10, key: 'quilisma', name: 'Quilisma', description: 'Ornamental neume', active: true },
  { id: 11, key: 'stropha', name: 'Stropha', description: 'Repeated note with special articulation', active: true },
  { id: 12, key: 'pressus', name: 'Pressus', description: 'Compound neume with held note', active: true },
  { id: 13, key: 'bistropha', name: 'Bistropha', description: 'Two strophae', active: true },
  { id: 14, key: 'tristropha', name: 'Tristropha', description: 'Three strophae', active: true },
  { id: 15, key: 'bivirga', name: 'Bivirga', description: 'Two virgae on same pitch', active: true },
  { id: 16, key: 'trivirga', name: 'Trivirga', description: 'Three virgae on same pitch', active: true },
  { id: 17, key: 'pes subbipunctis', name: 'Pes Subbipunctis', description: 'Pes followed by two descending puncta', active: true },
  { id: 18, key: 'scandicus flexus', name: 'Scandicus Flexus', description: 'Scandicus with descending final note', active: true },
  { id: 19, key: 'torculus resupinus', name: 'Torculus Resupinus', description: 'Torculus with ascending final note', active: true },
  { id: 20, key: 'porrectus flexus', name: 'Porrectus Flexus', description: 'Porrectus with descending final note', active: true },
  { id: 21, key: 'uncinus', name: 'Uncinus', description: 'Hook-shaped neume', active: true },
  { id: 22, key: 'celeriter', name: 'Celeriter', description: 'Quick descending-ascending figure', active: true },
  { id: 23, key: 'salicus', name: 'Salicus', description: 'Ascending with rhythmic marking', active: true },
  { id: 24, key: 'apostropha', name: 'Apostropha', description: 'Liquescent note', active: true },
  { id: 25, key: 'virga episema', name: 'Virga episema', description: 'Single note with stem, with episema', active: true },
  { id: 26, key: 'clivis episema', name: 'Clivis episema', description: 'Two notes descending, with episema', active: true },
  { id: 27, key: 'climacus episema', name: 'Climacus episema', description: 'Three+ notes descending, with episema', active: true },
  { id: 28, key: 'apostropha episema', name: 'Apostropha episema', description: 'Liquescent note, with episema', active: true },
  { id: 29, key: 'cephalicus', name: 'Cephalicus', description: 'Liquescent descending neume', active: true },
  { id: 30, key: 'equaliter', name: 'Equaliter', description: 'Repeated equal-pitch motion', active: true },
  { id: 31, key: 'inferius', name: 'Inferius', description: 'Lower auxiliary neume', active: true },
  { id: 32, key: 'levare', name: 'Levare', description: 'Rising preparatory neume', active: true },
  { id: 33, key: 'mediocriter', name: 'Mediocriter', description: 'Moderately inflected neume', active: true },
  { id: 34, key: 'pressionem', name: 'Pressionem', description: 'Pressing/emphatic compound neume', active: true },
  { id: 35, key: 'sursum', name: 'Sursum', description: 'Upward-directed auxiliary neume', active: true },
  { id: 36, key: 'trigon', name: 'Trigon', description: 'Triangular-shaped note', active: true },
  { id: 37, key: 'pes liquescens', name: 'Pes Liquescens', description: 'Ascending two-note neume with liquescent ending', active: true },
  { id: 38, key: 'torculus liquescens', name: 'Torculus Liquescens', description: 'Low-high-low neume with liquescent ending', active: true },
  { id: 39, key: 'pes quadratus', name: 'Pes Quadratus', description: 'Ascending two-note neume with square form', active: true },
  { id: 40, key: 'pes quadratus subbipunctis', name: 'Pes Quadratus Subbipunctis', description: 'Pes quadratus followed by two descending puncta', active: true },
  { id: 41, key: 'tenete', name: 'Tenete', description: 'Held/sustained note indication', active: true },
  { id: 42, key: 'porrectus subbipunctis', name: 'Porrectus Subbipunctis', description: 'Porrectus followed by two descending puncta', active: true },
  { id: 43, key: 'expectate', name: 'Expectate', description: 'Extended concluding neume formula', active: true },
  { id: 44, key: 'scandicus climacus', name: 'Scandicus Climacus', description: 'Ascending then descending notes (scandicus + climacus)', active: true },
  { id: 45, key: 'pes subtripunctis', name: 'Pes Subtripunctis', description: 'Pes followed by three descending puncta', active: true },
  { id: 46, key: 'pes praebipunctis', name: 'Pes Praebipunctis', description: 'Two ascending puncta preceding a pes', active: true },
  { id: 47, key: 'clivis episema praebipunctis', name: 'Clivis Episema Praebipunctis', description: 'Two ascending puncta preceding a clivis with episema', active: true },
];

export function getActiveNeumeClasses(classes: NeumeClass[]): NeumeClass[] {
  return classes.filter((entry) => entry.active);
}

export function findNeumeClassByKey(
  classes: NeumeClass[],
  key: string | null | undefined
): NeumeClass | null {
  if (!key) return null;
  const normalized = key.trim().toLowerCase();
  return classes.find((entry) => entry.key.toLowerCase() === normalized) || null;
}

export function findNeumeClassBySuggestion(
  classes: NeumeClass[],
  suggestion: string | null | undefined
): NeumeClass | null {
  if (!suggestion) return null;
  const normalized = suggestion.trim().toLowerCase();
  return classes.find((entry) =>
    entry.key.toLowerCase() === normalized || entry.name.toLowerCase() === normalized
  ) || null;
}
