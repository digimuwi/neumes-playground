## Context

The toolbar currently renders 7 buttons in its first group: Import Image (via `ImageUploader` component), Export MEI, Export JSON, Import JSON, Browse Contributions, Contribute, and Train. The import/export buttons are individual `IconButton` components that directly trigger their respective actions.

The `ImageUploader` component owns its own hidden file input and icon button. The JSON import uses a separate hidden file input in `Toolbar.tsx`. Both export buttons call their respective export functions directly on click.

## Goals / Non-Goals

**Goals:**
- Consolidate 4 import/export buttons into 2 dropdown menus (Import, Export)
- Keep the contributions group (Browse, Contribute, Train) unchanged after a divider
- Maintain all existing import/export behavior exactly

**Non-Goals:**
- Changing any import/export logic or data formats
- Adding new import/export formats
- Changing the contributions, OCR, or undo/redo groups

## Decisions

### 1. Use MUI Menu component for dropdowns

Use MUI's `Menu` + `MenuItem` for the dropdown menus, anchored to `Button` components (not `IconButton`).

**Rationale:** `Menu` is the standard MUI pattern for dropdown actions. Using `Button` with text labels ("Import", "Export") plus a dropdown arrow icon provides clearer affordance than icon-only buttons, since the dropdown behavior needs to be discoverable.

**Alternative considered:** `IconButton` with `Popover` — rejected because text labels are more scannable when grouping multiple actions behind a single control.

### 2. Inline ImageUploader logic into Toolbar

Move the image file input and handler from the standalone `ImageUploader` component directly into `Toolbar.tsx`, alongside the existing JSON file input. The "Import Image" menu item will programmatically click the hidden image file input, same pattern as JSON import already uses.

**Rationale:** `ImageUploader` exists solely to wrap a file input with an icon button. With the button moving into a menu item, the component's only remaining purpose would be the hidden input and its `onChange` handler — not worth a separate component.

**Alternative considered:** Keep `ImageUploader` and expose an imperative `trigger()` ref — adds indirection for no benefit since the logic is simple (5 lines).

### 3. Disabled state on individual menu items

The Import/Export buttons themselves are always enabled and clickable. Individual menu items are disabled based on state:
- Export MEI: disabled when no image loaded
- Export JSON: disabled when no image loaded
- Import Image: always enabled
- Import JSON: always enabled

**Rationale:** Per user decision. Keeping the parent buttons always enabled ensures discoverability — users can always see what actions exist even if some aren't currently available.

## Risks / Trade-offs

- **Extra click for common actions** → The most frequent action (Import Image) now requires 2 clicks instead of 1. Acceptable trade-off for a cleaner toolbar since image import is typically done once per session.
- **ImageUploader component removal** → If anything else imports `ImageUploader`, it would break. Currently only `Toolbar.tsx` uses it, so this is safe. The file can be deleted.
