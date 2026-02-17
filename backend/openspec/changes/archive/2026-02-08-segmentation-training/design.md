## Context

The recognition pipeline uses Kraken's default `blla.mlmodel` for baseline segmentation. This model occasionally places baselines through neume regions, causing garbage OCR and incorrect text masking. We tried post-hoc filtering (confidence-based, uppercase heuristics) but the signals are too weak — the model is confidently wrong.

The existing YOLO training pipeline (`yolo_trainer.py` → `yolo_export.py`) provides a pattern: export contribution data to a training format, train a model, version it, deploy atomically. Segmentation training follows the same pattern but targets Kraken instead of ultralytics.

Contributions contain: line boundary polygons, syllable boundaries with text, and neume bounding boxes — enough to generate Kraken's required baselines and typed regions.

## Goals / Non-Goals

**Goals:**
- Fine-tune Kraken's default segmentation model using contribution data
- Teach the model to distinguish text regions (put baselines here) from neume regions (don't)
- Run segmentation training alongside YOLO training, triggered from the same API
- Deploy custom models atomically, fall back to default when none exists

**Non-Goals:**
- Training a recognition (OCR) model — only segmentation
- Replacing the default model for all users — just supplementing it with a fine-tuned version
- Real-time training progress for segmentation (Kraken doesn't expose epoch callbacks as easily as ultralytics)

## Decisions

**Baseline computation: syllable bottom-center polyline**

For each line, collect the bottom-center point of each syllable boundary polygon, sort by X, and connect as a polyline. This gives the text baseline because syllable boundaries precisely mark where text characters sit.

Alternative considered: extracting the bottom edge of the line boundary polygon. Rejected because line boundaries encompass both text and neume areas, so the bottom edge may not correspond to the actual text baseline.

**Neume region construction: group neumes per text line into bounding rectangles**

For each text line, collect all neume bboxes whose vertical center falls between the previous line's baseline Y and the current line's baseline Y (or image top for the first line). Compute the bounding rectangle of the group. Tag as region type `neume`.

Text regions are constructed from the line boundary polygons, tagged as `text`.

**Region types: `text` and `neume`**

Two region types taught to the model. The `--resize union` flag when fine-tuning from the default model adds these types without losing the default's existing knowledge.

**Export format: PageXML**

Kraken natively parses PageXML. Each contribution becomes one PageXML file paired with its image. PageXML structure: `<Page>` → `<TextRegion>` and custom `<ImageRegion>` (for neumes) → `<TextLine>` with `<Baseline>` and `<Coords>`.

**Training API: Kraken's `SegmentationModel` from `kraken.lib.train`**

Call Kraken's Python training API directly rather than shelling out to `ketos segtrain`. This keeps training in-process and consistent with how YOLO training works (both are Python API calls in a background thread).

Key parameters:
- `-i blla.mlmodel` equivalent: `model=<path_to_default_model>`
- `--resize union`: adds new region types to the existing model
- Epochs, learning rate, device configurable

**Orchestration: independent threads from `start_training()`**

`start_training()` launches two daemon threads: one for YOLO, one for segmentation. They share no state and run independently. Training status tracks both — state is `"complete"` only when both finish.

**Model deployment: same pattern as YOLO**

Versioned saves to `models/seg_versions/<timestamp>.mlmodel`, atomic deploy to `models/seg_model.mlmodel` via write-to-temp + `os.replace()`.

**Model loading: prefer custom, fall back to default**

`segment_image()` checks if `models/seg_model.mlmodel` exists. If yes, loads it. If no, uses Kraken's built-in default. Model is cached at module level (same pattern as recognition model caching in `recognition.py`).

## Risks / Trade-offs

- **Small dataset (5-6 contributions, ~91 lines)** → Fine-tuning from a pretrained model helps, but results may be limited. Mitigation: this is meant to improve iteratively as more contributions arrive. Each training run uses all available data.
- **Kraken training API stability** → `kraken.lib.train.SegmentationModel` is less documented than the CLI. Mitigation: inspect the `ketos segtrain` source (which wraps the same API) to ensure correct usage.
- **Training time** → Segmentation training on CPU/MPS may be slow for large images. Mitigation: Kraken internally rescales images to a fixed height (1800px default). Start with few epochs (e.g., 50) and tune.
- **Gradient tracking gotcha** → Kraken's `blla.segment()` disables PyTorch gradients. Segmentation training itself should be unaffected (it manages its own gradient state), but the existing `torch.set_grad_enabled(True)` fix before YOLO training remains necessary.
