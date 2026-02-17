## 1. Layout Changes

- [x] 1.1 Remove AnnotationList and AnnotationEditor imports from App.tsx
- [x] 1.2 Remove sidebar Box container from App.tsx layout
- [x] 1.3 Update canvas container to take full width
- [x] 1.4 Delete src/components/AnnotationList.tsx
- [x] 1.5 Delete src/components/AnnotationEditor.tsx

## 2. Inline Popover Component

- [x] 2.1 Create src/components/InlineAnnotationEditor.tsx with type toggle (radio buttons)
- [x] 2.2 Add syllable text field input with Enter key handler to close
- [x] 2.3 Add neume type dropdown with onChange handler to close
- [x] 2.4 Add Escape key handler to close popover
- [x] 2.5 Style popover with fixed 280px width and appropriate padding

## 3. Popover Positioning

- [x] 3.1 Add position calculation in AnnotationCanvas using screen coordinate transforms
- [x] 3.2 Implement right-side preferred positioning with 8px gap
- [x] 3.3 Implement left-side fallback when near right edge
- [x] 3.4 Implement vertical adjustment when near bottom edge
- [x] 3.5 Ensure position updates on zoom/pan changes

## 4. Popover Integration

- [x] 4.1 Render InlineAnnotationEditor inside AnnotationCanvas container
- [x] 4.2 Pass selected annotation data and screen position to popover
- [x] 4.3 Implement click-outside detection to close popover (excluding clicks on other annotations)
- [x] 4.4 Wire up auto-focus for newly created annotations (reuse isNewlyCreated flag)

## 5. Keyboard Navigation

- [x] 5.1 Add reading order sort function for annotations (Y primary, X secondary with 2% threshold)
- [x] 5.2 Implement Tab key handler to select next annotation in reading order
- [x] 5.3 Implement Shift+Tab handler to select previous annotation
- [x] 5.4 Add wrap-around behavior (last→first, first→last)
- [x] 5.5 Ensure Tab navigation only triggers when canvas/popover is focused (not inside text field)
