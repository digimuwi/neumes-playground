## 1. Remove PAGE XML

- [x] 1.1 Delete `contribution/page_xml.py`
- [x] 1.2 Remove `generate_page_xml` from `contribution/__init__.py` exports

## 2. Rewrite storage

- [x] 2.1 Rewrite `contribution/storage.py` — `save_contribution()` accepts annotations dict + image metadata, writes `annotations.json` instead of `page.xml`
- [x] 2.2 Add image metadata construction (filename, width, height) to the stored JSON

## 3. Update /contribute endpoint

- [x] 3.1 Update `/contribute` in `api.py` — remove PAGE XML generation, remove neume discarding, pass annotations + image metadata to new `save_contribution()`
- [x] 3.2 Remove `generate_page_xml` import from `api.py`

## 4. Rewrite tests

- [x] 4.1 Remove all PAGE XML test helpers and assertions from `test_contribution.py`
- [x] 4.2 Add tests for `annotations.json` storage — verify JSON file exists, contains correct image metadata, lines, and neumes
- [x] 4.3 Add test that neumes are stored (not discarded)
- [x] 4.4 Add test that annotations are stored verbatim (trailing hyphens preserved)
- [x] 4.5 Add test that any neume type string is accepted

## 5. Update spec

- [x] 5.1 Verify all spec scenarios from the delta have corresponding test coverage
