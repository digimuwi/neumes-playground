## Why

Kraken's segmentation sometimes identifies neume regions as text lines. During training export, the system re-runs Kraken segmentation and masks ALL detected text regions — including those the user corrected by removing syllable boxes on the client. This means user corrections don't flow into training data: neumes under wrongly-identified text lines get erased from training images, so the model never learns them. Additionally, the current rectangular syllable bounding boxes provide a crude visual representation on the client compared to the precise boundary polygons Kraken already computes.

## What Changes

- **BREAKING**: `/recognize` response restructured — syllables are nested under their parent lines instead of a flat list with `line_index`. Each line gains a `boundary` polygon field. Each syllable gains a `boundary` polygon field (sliced from the parent line polygon at character cut positions using Shapely).
- **BREAKING**: `/contribute` request and storage format restructured — lines contain `boundary` polygon, syllables contain `boundary` polygon instead of `bbox`. The stored `annotations.json` changes shape accordingly.
- Text masking during training export uses contributed syllable polygons instead of re-running Kraken segmentation. Only regions the user confirmed as text get masked.
- `mask_text_regions` gains an alternative entry point accepting a list of polygon coordinate lists (from stored annotations) rather than requiring a Kraken `Segmentation` object.
- New geometry function to slice a line boundary polygon into per-syllable polygons using character cut positions.
- One-time migration script to backfill existing contributions with polygon data by re-running segmentation + OCR and matching against existing syllable annotations.

## Capabilities

### New Capabilities
- `syllable-polygon-slicing`: Geometry logic to slice a line boundary polygon into per-syllable polygons at character cut boundaries using Shapely intersection.
- `contribution-migration`: One-time script to backfill existing contribution annotations with syllable polygon boundaries derived from re-running the recognition pipeline.

### Modified Capabilities
- `training-data-contribution`: Annotation input structure changes — lines gain `boundary` polygon field, syllables use `boundary` polygon instead of `bbox`. Storage format changes accordingly.
- `text-masking`: `mask_text_regions` gains ability to accept a flat list of polygon coordinate lists (from annotations) as an alternative to a Kraken `Segmentation` object.
- `yolo-training-export`: Export no longer re-runs Kraken segmentation. Instead loads contributed syllable polygons from `annotations.json` and passes them to `mask_text_regions`.
- `neume-annotation-response`: Response structure changes — lines include `boundary` polygon, syllables include `boundary` polygon and are nested under lines instead of flat with `line_index`.

## Impact

- **API**: Both `/recognize` response and `/contribute` request shapes change (breaking for frontend)
- **Storage**: `annotations.json` format changes (migration script needed for 4 existing contributions)
- **Training pipeline**: Export no longer calls `segment_image()`, uses stored polygon data instead
- **Dependencies**: Shapely already present, no new dependencies
- **Code**: Changes to `api.py`, `types.py`, `storage.py`, `text_masking.py`, `yolo_export.py`, `geometry.py`; new slicing module; new migration script
