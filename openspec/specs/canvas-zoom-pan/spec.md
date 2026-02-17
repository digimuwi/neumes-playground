### Requirement: Zoom with mouse wheel

The canvas SHALL zoom in when the user scrolls up while holding Ctrl (or Cmd on Mac), and zoom out when scrolling down with the modifier held. Zoom SHALL be anchored at the current mouse cursor position.

#### Scenario: Zoom in at cursor
- **WHEN** user holds Ctrl and scrolls up with mouse over canvas
- **THEN** canvas zooms in, keeping the point under the cursor stationary

#### Scenario: Zoom out at cursor
- **WHEN** user holds Ctrl and scrolls down with mouse over canvas
- **THEN** canvas zooms out, keeping the point under the cursor stationary

#### Scenario: No zoom without modifier
- **WHEN** user scrolls without holding Ctrl/Cmd
- **THEN** canvas zoom level SHALL NOT change

### Requirement: Zoom limits

The zoom level SHALL be constrained between 0.5x (50%) and 5x (500%) of the fit-to-container size.

#### Scenario: Minimum zoom enforced
- **WHEN** user attempts to zoom out below 0.5x
- **THEN** zoom level remains at 0.5x

#### Scenario: Maximum zoom enforced
- **WHEN** user attempts to zoom in above 5x
- **THEN** zoom level remains at 5x

### Requirement: Pan with Space+drag

The canvas SHALL enter pan mode when the Space key is held. In pan mode, dragging the mouse SHALL pan the view instead of drawing annotations.

#### Scenario: Enter pan mode
- **WHEN** user presses and holds Space key
- **THEN** cursor changes to grab cursor and canvas enters pan mode

#### Scenario: Pan the view
- **WHEN** user drags mouse while in pan mode
- **THEN** the visible portion of the canvas moves with the drag direction

#### Scenario: Exit pan mode
- **WHEN** user releases Space key
- **THEN** cursor returns to crosshair and canvas returns to draw mode

#### Scenario: Pan mode does not draw
- **WHEN** user clicks and drags while holding Space
- **THEN** no annotation rectangle is created

### Requirement: Reset zoom

The canvas SHALL reset to fit-to-container view (zoom 1x, pan 0,0) when the user double-clicks on the canvas background (not on an annotation).

#### Scenario: Double-click resets view
- **WHEN** user double-clicks on canvas background (no annotation under cursor)
- **THEN** zoom resets to 1x and pan resets to (0,0)

#### Scenario: Double-click on annotation does not reset
- **WHEN** user double-clicks on an existing annotation
- **THEN** zoom and pan remain unchanged

### Requirement: Visual feedback for interaction mode

The cursor SHALL indicate the current interaction mode: crosshair for draw mode, grab for pan mode (Space held), grabbing while actively panning.

#### Scenario: Draw mode cursor
- **WHEN** canvas is in draw mode (Space not held)
- **THEN** cursor displays as crosshair

#### Scenario: Pan mode cursor
- **WHEN** Space is held but mouse is not dragging
- **THEN** cursor displays as grab (open hand)

#### Scenario: Panning cursor
- **WHEN** Space is held and mouse is dragging
- **THEN** cursor displays as grabbing (closed hand)

### Requirement: Annotation coordinates remain accurate

Annotations created while zoomed/panned SHALL be stored in normalized coordinates (0-1) relative to the original image dimensions, ensuring they appear at the correct position regardless of current zoom/pan state.

#### Scenario: Draw annotation while zoomed
- **WHEN** user draws a rectangle while zoomed in at 3x
- **THEN** the annotation is stored with normalized coordinates matching the image position, not the screen position

#### Scenario: Existing annotations render correctly after zoom
- **WHEN** user zooms or pans after creating annotations
- **THEN** all existing annotations remain visually aligned with their corresponding image regions
