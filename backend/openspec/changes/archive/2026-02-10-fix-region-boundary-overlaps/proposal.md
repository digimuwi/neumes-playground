## Why

The Kraken segmentation model suffers from catastrophic forgetting during fine-tuning because TextRegion and MusicRegion boundaries overlap by 20-50px vertically across the full page width. Kraken does pixel-level classification, so overlapping regions create conflicting training labels — the same pixels are labeled as both "text" and "neume".

## What Changes

- Clip TextRegion and MusicRegion boundaries at the vertical midpoint of their overlap zone so no pixel belongs to more than one region
- Add a polygon clipping utility that truncates a boundary polygon at a horizontal Y threshold
- The alternating neume-text-neume-text region structure and `type` attributes are preserved as-is

## Capabilities

### New Capabilities

### Modified Capabilities
- `segmentation-training-export`: Region boundaries must be non-overlapping via midpoint clipping

## Impact

- `src/htr_service/training/seg_export.py`: `build_pagexml()` gains a boundary clipping pass after building all regions
- Exported PageXML files in `datasets/segmentation/` will have non-overlapping regions
- No API changes; no dependency changes
