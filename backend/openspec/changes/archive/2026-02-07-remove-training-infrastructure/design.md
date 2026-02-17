## Context

Change 1 removed neume-as-lines from the recognition pipeline. The Kraken training infrastructure remains fully wired: `storage.py` calls `increment_count()` + `check_and_trigger_training()` on every contribution, `page_xml.py` groups neumes into bands for Kraken segtrain/train, and the `training/` module implements orchestration, triggers, locking, and PAGE XML filtering. None of this code serves a purpose anymore.

The `/contribute` endpoint currently accepts neumes and stores them as neume-typed TextLines in PAGE XML. Since neume training is moving to YOLO (Change 7-8), this PAGE XML representation is dead-end. Change 6 will replace PAGE XML storage entirely with JSON. For now, neumes in contributions are silently ignored.

## Goals / Non-Goals

**Goals:**
- Remove all Kraken training code, scripts, and obsolete model files
- Simplify `page_xml.py` to text-only (no neume bands)
- Disconnect training triggers from contribution storage
- Remove related tests
- Keep `/contribute` API contract unchanged (accepts neumes, doesn't error)

**Non-Goals:**
- Replacing PAGE XML with JSON (that's Change 6)
- Adding YOLO training infrastructure (that's Changes 7-8)
- Changing the `/contribute` API signature
- Modifying the `/recognize` endpoint (already done in Change 1)

## Decisions

### 1. Silently ignore neumes in `/contribute`

The `/contribute` endpoint still accepts `neumes` in annotations input. Rather than rejecting neume data (breaking change) or storing it in a dead format, we pass an empty neumes list to `generate_page_xml()`. The neume data is simply not persisted until Change 6 introduces JSON storage.

**Alternative considered**: Remove `neumes` from the API input schema entirely. Rejected because that's a breaking frontend change and Change 6 will redesign this endpoint anyway.

### 2. Keep `page_xml.py` with text-only generation

Remove `_group_neumes_into_bands()` and all neume band generation logic from `generate_page_xml()`. The function still generates valid PAGE XML for text lines. The `NeumeInput` import and neume parameter in `ContributionAnnotations` remain (used by the API input model) but `page_xml.py` no longer references them.

**Alternative considered**: Delete `page_xml.py` entirely. Rejected because text contributions still need PAGE XML storage until Change 6.

### 3. Delete entire `training/` module

All four files (`orchestrator.py`, `triggers.py`, `lock.py`, `filter_page_xml.py`) plus `__init__.py` are removed as a unit. No code depends on them after `storage.py` is updated.

### 4. Delete `contribution/counter.py` and its exports

The counter only existed to drive training thresholds. With triggers gone, counting has no purpose. Remove from `contribution/__init__.py` exports.

### 5. Delete all training scripts and generated data

Four scripts removed: `trigger_training.py`, `generate_synthetic_data.py`, `compose_manuscripts.py`, `generate_from_contribution.py`. Also remove the `synthetic_data/` directory they generated and the `contributions/.count` file.

### 6. Delete obsolete model files

Remove `segmentation_old.mlmodel`, `segmentation_broken.mlmodel`, `recognition_neume.mlmodel`, and `training.log` from `models/`. These are Kraken models that are no longer loaded or trained.

## Risks / Trade-offs

**[Neume contributions silently lost]** → Acceptable trade-off. No neume data is currently being collected in production (counter shows only 2 test contributions). Change 6 will add proper neume storage. Documented in proposal as transitional.

**[PAGE XML still generated but not used for training]** → PAGE XML contributions continue to be stored on disk but nothing consumes them for training. This is intentional — the storage format persists as an archive until Change 6 replaces it.

**[`contributions/.count` file deleted]** → The count (currently 2) has no value since training thresholds no longer exist. Safe to delete.
