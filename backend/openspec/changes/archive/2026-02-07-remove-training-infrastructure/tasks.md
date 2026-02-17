## 1. Delete training module

- [x] 1.1 Delete `src/htr_service/training/orchestrator.py`, `triggers.py`, `lock.py`, `filter_page_xml.py`, and `__init__.py`

## 2. Delete contribution counter

- [x] 2.1 Delete `src/htr_service/contribution/counter.py`
- [x] 2.2 Remove `increment_count` and `read_count` exports from `contribution/__init__.py`

## 3. Disconnect training from storage

- [x] 3.1 Remove training trigger imports and calls from `storage.py` (lines 68-73)

## 4. Simplify page_xml.py to text-only

- [x] 4.1 Remove `_group_neumes_into_bands()` function and neume band generation logic (lines 43-81, 156-186) from `page_xml.py`
- [x] 4.2 Remove `NeumeInput` import from `page_xml.py`

## 5. Ignore neumes in /contribute endpoint

- [x] 5.1 Update `/contribute` in `api.py` to pass empty neumes list to `generate_page_xml()` (silently ignore neume input)

## 6. Delete scripts

- [x] 6.1 Delete `scripts/trigger_training.py`, `scripts/generate_synthetic_data.py`, `scripts/compose_manuscripts.py`, `scripts/generate_from_contribution.py`

## 7. Delete obsolete model files and generated data

- [x] 7.1 Delete `models/segmentation_old.mlmodel`, `models/segmentation_broken.mlmodel`, `models/recognition_neume.mlmodel`, `models/training.log`
- [x] 7.2 Delete `synthetic_data/` directory
- [x] 7.3 Delete `contributions/.count` file

## 8. Update tests

- [x] 8.1 Delete `tests/test_filter_page_xml.py`, `tests/test_training_integration.py`, `tests/test_counter.py`
- [x] 8.2 Remove neume band grouping tests from `tests/test_contribution.py` (tests for `_group_neumes_into_bands` and neume-band PAGE XML scenarios)
- [x] 8.3 Update remaining contribution tests to reflect that neumes are silently ignored (neume-only contributions produce empty PAGE XML)
- [x] 8.4 Run full test suite and verify all tests pass
