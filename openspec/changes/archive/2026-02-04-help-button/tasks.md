## 1. Help Button Component

- [x] 1.1 Create `src/components/HelpButton.tsx` with MUI Fab and HelpOutline icon
- [x] 1.2 Add local state for dialog open/close
- [x] 1.3 Style Fab with fixed positioning (bottom-right, above canvas)

## 2. Help Dialog Content

- [x] 2.1 Create MUI Dialog with compact sizing (maxWidth: 'sm')
- [x] 2.2 Add platform detection helper for modifier key display (⌘ vs Ctrl)
- [x] 2.3 Add "Navigate the Image" section (zoom, pan, reset)
- [x] 2.4 Add "Cycle Through Annotations" section (Tab, Shift+Tab, Select All, Escape, Delete)
- [x] 2.5 Add "Drawing & OCR" section (click+drag, Shift+drag)
- [x] 2.6 Add "Undo / Redo" section
- [x] 2.7 Add "Tips" section (assignment curves, auto-tightening, suggestions)
- [x] 2.8 Style content for scannability (section headers, key badges, descriptions)

## 3. Keyboard Shortcut Integration

- [x] 3.1 Add `?` key handler in AnnotationCanvas.tsx keydown listener
- [x] 3.2 Guard handler to skip when text input is focused
- [x] 3.3 Expose callback prop or use context to trigger dialog from keyboard

## 4. App Integration

- [x] 4.1 Import and render HelpButton in App.tsx or AnnotationCanvas.tsx
- [x] 4.2 Verify Fab positioning doesn't interfere with canvas interactions
- [x] 4.3 Test dialog open/close via button click, ? key, and Escape
