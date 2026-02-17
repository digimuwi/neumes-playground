import { NeumeType } from '../state/types';

export interface NeumeTypeInfo {
  type: NeumeType;
  name: string;
  description: string;
}

export const neumeTypes: NeumeTypeInfo[] = [
  // Basic neumes
  {
    type: NeumeType.PUNCTUM,
    name: 'Punctum',
    description: 'Single note (dot)',
  },
  {
    type: NeumeType.VIRGA,
    name: 'Virga',
    description: 'Single note with stem',
  },

  // Two-note neumes
  {
    type: NeumeType.PES,
    name: 'Pes',
    description: 'Two notes ascending',
  },
  {
    type: NeumeType.CLIVIS,
    name: 'Clivis',
    description: 'Two notes descending',
  },

  // Three-note neumes
  {
    type: NeumeType.TORCULUS,
    name: 'Torculus',
    description: 'Three notes: low-high-low',
  },
  {
    type: NeumeType.PORRECTUS,
    name: 'Porrectus',
    description: 'Three notes: high-low-high',
  },
  {
    type: NeumeType.SCANDICUS,
    name: 'Scandicus',
    description: 'Three notes ascending',
  },
  {
    type: NeumeType.CLIMACUS,
    name: 'Climacus',
    description: 'Three+ notes descending',
  },

  // Compound neumes
  {
    type: NeumeType.PES_SUBBIPUNCTIS,
    name: 'Pes Subbipunctis',
    description: 'Pes followed by two descending puncta',
  },
  {
    type: NeumeType.PES_SUBTRIPUNCTIS,
    name: 'Pes Subtripunctis',
    description: 'Pes followed by three descending puncta',
  },
  {
    type: NeumeType.PES_PRAEBIPUNCTIS,
    name: 'Pes Praebipunctis',
    description: 'Two ascending puncta preceding a pes',
  },
  {
    type: NeumeType.SCANDICUS_FLEXUS,
    name: 'Scandicus Flexus',
    description: 'Scandicus with descending final note',
  },
  {
    type: NeumeType.TORCULUS_RESUPINUS,
    name: 'Torculus Resupinus',
    description: 'Torculus with ascending final note',
  },
  {
    type: NeumeType.PORRECTUS_FLEXUS,
    name: 'Porrectus Flexus',
    description: 'Porrectus with descending final note',
  },
  {
    type: NeumeType.SCANDICUS_CLIMACUS,
    name: 'Scandicus Climacus',
    description: 'Ascending then descending notes (scandicus + climacus)',
  },

  // Repeated notes
  {
    type: NeumeType.BIVIRGA,
    name: 'Bivirga',
    description: 'Two virgae on same pitch',
  },
  {
    type: NeumeType.TRIVIRGA,
    name: 'Trivirga',
    description: 'Three virgae on same pitch',
  },
  {
    type: NeumeType.STROPHA,
    name: 'Stropha',
    description: 'Repeated note with special articulation',
  },
  {
    type: NeumeType.BISTROPHA,
    name: 'Bistropha',
    description: 'Two strophae',
  },
  {
    type: NeumeType.TRISTROPHA,
    name: 'Tristropha',
    description: 'Three strophae',
  },

  // Special neumes
  {
    type: NeumeType.PRESSUS,
    name: 'Pressus',
    description: 'Compound neume with held note',
  },
  {
    type: NeumeType.UNCINUS,
    name: 'Uncinus',
    description: 'Hook-shaped neume',
  },
  {
    type: NeumeType.CELERITER,
    name: 'Celeriter',
    description: 'Quick descending-ascending figure',
  },
  {
    type: NeumeType.QUILISMA,
    name: 'Quilisma',
    description: 'Ornamental neume',
  },
  {
    type: NeumeType.SALICUS,
    name: 'Salicus',
    description: 'Ascending with rhythmic marking',
  },
  {
    type: NeumeType.APOSTROPHA,
    name: 'Apostropha',
    description: 'Liquescent note',
  },

  // Episema variants
  {
    type: NeumeType.VIRGA_EPISEMA,
    name: 'Virga episema',
    description: 'Single note with stem, with episema',
  },
  {
    type: NeumeType.CLIVIS_EPISEMA,
    name: 'Clivis episema',
    description: 'Two notes descending, with episema',
  },
  {
    type: NeumeType.CLIVIS_EPISEMA_PRAEBIPUNCTIS,
    name: 'Clivis Episema Praebipunctis',
    description: 'Two ascending puncta preceding a clivis with episema',
  },
  {
    type: NeumeType.CLIMACUS_EPISEMA,
    name: 'Climacus episema',
    description: 'Three+ notes descending, with episema',
  },
  {
    type: NeumeType.APOSTROPHA_EPISEMA,
    name: 'Apostropha episema',
    description: 'Liquescent note, with episema',
  },

  // Liquescent and quadratus variants
  {
    type: NeumeType.ORISCUS,
    name: 'Oriscus',
    description: 'Ornamental wavy note',
  },
  {
    type: NeumeType.TRIGON,
    name: 'Trigon',
    description: 'Triangular-shaped note',
  },
  {
    type: NeumeType.PES_LIQUESCENS,
    name: 'Pes Liquescens',
    description: 'Ascending two-note neume with liquescent ending',
  },
  {
    type: NeumeType.TORCULUS_LIQUESCENS,
    name: 'Torculus Liquescens',
    description: 'Low-high-low neume with liquescent ending',
  },
  {
    type: NeumeType.PES_QUADRATUS,
    name: 'Pes Quadratus',
    description: 'Ascending two-note neume with square form',
  },
  {
    type: NeumeType.PES_QUADRATUS_SUBBIPUNCTIS,
    name: 'Pes Quadratus Subbipunctis',
    description: 'Pes quadratus followed by two descending puncta',
  },
  {
    type: NeumeType.TENETE,
    name: 'Tenete',
    description: 'Held/sustained note indication',
  },
  {
    type: NeumeType.PORRECTUS_SUBBIPUNCTIS,
    name: 'Porrectus Subbipunctis',
    description: 'Porrectus followed by two descending puncta',
  },
  {
    type: NeumeType.EXPECTATE,
    name: 'Expectate',
    description: 'Wait/pause indication',
  },

  // Additional neume types
  {
    type: NeumeType.CEPHALICUS,
    name: 'Cephalicus',
    description: 'Liquescent descending neume',
  },
  {
    type: NeumeType.EQUALITER,
    name: 'Equaliter',
    description: 'Equal rhythmic value indication',
  },
  {
    type: NeumeType.INFERIUS,
    name: 'Inferius',
    description: 'Lower pitch indication',
  },
  {
    type: NeumeType.LEVARE,
    name: 'Levare',
    description: 'Upward melodic movement',
  },
  {
    type: NeumeType.MEDIOCRITER,
    name: 'Mediocriter',
    description: 'Moderate rhythmic value',
  },
  {
    type: NeumeType.PRESSIONEM,
    name: 'Pressionem',
    description: 'Pressure/emphasis marking',
  },
  {
    type: NeumeType.SURSUM,
    name: 'Sursum',
    description: 'Upward direction indicator',
  },
];
