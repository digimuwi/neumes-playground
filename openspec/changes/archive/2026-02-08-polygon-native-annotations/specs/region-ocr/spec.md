## MODIFIED Requirements

### Requirement: OCR region uses pixel coordinates
The system SHALL convert the normalized draw region to pixel coordinates when calling the backend. The backend returns syllables nested inside lines with polygon boundaries. The system SHALL normalize returned polygon coordinates to 0-1 for annotation storage.

#### Scenario: Coordinate transformation round-trip
- **WHEN** user draws a region at normalized coords (0.1, 0.2, 0.3, 0.4) on a 1000x800 image
- **THEN** backend receives pixel region {x: 100, y: 160, width: 300, height: 320}
- **THEN** returned syllable polygon boundaries are normalized from pixel to 0-1 coordinates for annotation storage

#### Scenario: Nested line/syllable response is parsed correctly
- **WHEN** the backend returns `{ lines: [{ text: "Glo-ri-a", boundary: [...], syllables: [{ text: "Glo-", boundary: [[100,200],[200,200],[200,250],[100,250]], confidence: 0.9 }] }], neumes: [...] }`
- **THEN** a syllable annotation is created with `polygon: [[0.1,0.25],[0.2,0.25],[0.2,0.3125],[0.1,0.3125]]` (normalized against image dimensions)
- **THEN** the neume annotations are created with 4-corner polygons converted from their bboxes
