## 1. Extract Pure Functions from Hooks

- [x] 1.1 Extract text line grouping logic from `useTextLines` into a pure function `computeTextLines(annotations)`
- [x] 1.2 Extract neume assignment logic from `useNeumeAssignment` into a pure function `computeNeumeAssignments(annotations, textLines)`
- [x] 1.3 Update hooks to call the extracted pure functions (maintain backward compatibility)

## 2. MEI Generation Core

- [x] 2.1 Create `src/utils/meiExport.ts` with type definitions for image dimensions
- [x] 2.2 Implement `getImageDimensions(dataUrl)` async function to extract width/height from base64 image
- [x] 2.3 Implement `denormalizeRect(rect, dimensions)` to convert normalized coords to pixels
- [x] 2.4 Implement `generateZones(annotations, dimensions)` to create zone XML strings
- [x] 2.5 Implement `getSyllablesInReadingOrder(annotations, textLines)` to sort syllables by line then x-position
- [x] 2.6 Implement `groupNeumesBySyllable(annotations, assignments)` to build Map<syllableId, neume[]> sorted by x
- [x] 2.7 Implement `generateSyllableXML(syllable, neumes)` to create syllable element with nested neumes
- [x] 2.8 Implement `generateMEI(annotations, dimensions)` main function assembling full MEI document

## 3. Download Trigger

- [x] 3.1 Implement `downloadMEI(xmlString, filename)` utility to trigger browser download
- [x] 3.2 Implement `exportMEI(annotations, imageDataUrl)` orchestrator that gets dimensions and triggers download

## 4. UI Integration

- [x] 4.1 Add "Export MEI" button to Toolbar component
- [x] 4.2 Wire button click to call `exportMEI` with current state
- [x] 4.3 Disable button when no image is loaded
