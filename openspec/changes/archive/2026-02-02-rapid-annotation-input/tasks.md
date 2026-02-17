## 1. State Changes for Tracking New Annotations

- [x] 1.1 Add `isNewlyCreated` flag to AppState type
- [x] 1.2 Add CLEAR_NEW_FLAG action type
- [x] 1.3 Update ADD_ANNOTATION handler to set `isNewlyCreated: true`
- [x] 1.4 Add CLEAR_NEW_FLAG handler to set `isNewlyCreated: false`
- [x] 1.5 Add clearNewFlag action creator

## 2. Sticky Type Implementation

- [x] 2.1 Update addAnnotation action to accept optional type parameter
- [x] 2.2 Modify AnnotationCanvas to pass last annotation's type when creating new annotation
- [x] 2.3 Update ADD_ANNOTATION handler to use provided type or default to syllable

## 3. Auto-Focus Implementation

- [x] 3.1 Add inputRef to TextField in AnnotationEditor
- [x] 3.2 Add selectRef to Select in AnnotationEditor
- [x] 3.3 Add useEffect to focus appropriate input when isNewlyCreated is true
- [x] 3.4 Dispatch clearNewFlag after focusing
