## Why

The new neume detection pipeline (YOLOv8 + SAHI) needs text-free images to work effectively. Text characters and neume marks look similar at small scales, so running object detection on the raw manuscript image would produce false positives. We need a module that erases text from the RGB image using Kraken's boundary polygons, leaving only neume ink on parchment for the detector.

## What Changes

- Add a new `pipeline/text_masking.py` module that takes an RGB image and a Kraken `Segmentation` result as input
- Mask text regions by filling each line's boundary polygon with sampled parchment color (not flat white)
- Parchment color is sampled locally per polygon by dilating the boundary slightly and taking the median color of the ring between the original and dilated boundary
- Returns the masked RGB image with text erased and neumes preserved
- Pure image-processing module — no ML dependencies, only PIL/Pillow and numpy

## Capabilities

### New Capabilities
- `text-masking`: Erase text from manuscript images using Kraken segmentation boundary polygons, producing text-free RGB images suitable for neume object detection

### Modified Capabilities

## Impact

- **New file**: `src/htr_service/pipeline/text_masking.py`
- **New tests**: test coverage for the masking module
- **Dependencies**: No new dependencies — uses PIL and numpy already available in the environment
- **API**: No API changes — this module is internal, consumed by the neume detection pipeline (Change 4) and integrated into `/recognize` (Change 5)
