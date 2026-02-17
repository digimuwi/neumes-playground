## ADDED Requirements

### Requirement: Keyboard toggles for recognition modes
The system SHALL support two recognition modes — neume recognition and text recognition — toggled via keyboard shortcuts. Pressing `n` SHALL toggle neume recognition mode on/off. Pressing `t` SHALL toggle text recognition mode on/off. Pressing one mode key while the other mode is active SHALL switch to the pressed mode. Pressing `Escape` SHALL return to manual mode.

#### Scenario: Activate neume recognition mode
- **WHEN** user presses `n` while in manual mode
- **THEN** recognition mode changes to neume

#### Scenario: Deactivate neume recognition mode
- **WHEN** user presses `n` while in neume recognition mode
- **THEN** recognition mode returns to manual

#### Scenario: Switch from text to neume mode
- **WHEN** user presses `n` while in text recognition mode
- **THEN** recognition mode changes to neume

#### Scenario: Escape clears recognition mode
- **WHEN** user presses `Escape` while in any recognition mode
- **THEN** recognition mode returns to manual

#### Scenario: Keyboard shortcuts ignored in text inputs
- **WHEN** user presses `n` or `t` while focused on a text input or textarea
- **THEN** recognition mode does not change

### Requirement: Drawing in recognition mode triggers targeted backend request
When a recognition mode is active, drawing a rectangle SHALL send the region to the `/recognize` endpoint with the `type` parameter set to `"neume"` or `"text"` corresponding to the active mode. The system SHALL NOT create a manual annotation or open a dialog.

#### Scenario: Draw in neume recognition mode
- **WHEN** user draws a rectangle while neume recognition mode is active
- **THEN** system sends POST `/recognize` with `type="neume"` and the drawn region
- **THEN** system adds returned neume annotations to state
- **THEN** no syllable annotations are created (backend returns `lines=[]`)

#### Scenario: Draw in text recognition mode
- **WHEN** user draws a rectangle while text recognition mode is active
- **THEN** system sends POST `/recognize` with `type="text"` and the drawn region
- **THEN** system adds returned syllable annotations to state
- **THEN** no neume annotations are created (backend returns `neumes=[]`)

#### Scenario: Draw in manual mode unchanged
- **WHEN** user draws a rectangle while in manual mode
- **THEN** system creates a manual annotation with tightening (existing behavior)

### Requirement: Pulsing region indicator during recognition
While a targeted recognition request is in-flight, the system SHALL display the drawn region on the canvas with a pulsing (blinking) opacity animation. The animation SHALL stop and the region SHALL disappear when the response arrives.

#### Scenario: Region pulses during loading
- **WHEN** user draws a rectangle in a recognition mode and the request is in-flight
- **THEN** the drawn region is displayed on the canvas with smoothly oscillating opacity
- **THEN** the region uses the preview color style (green, dashed border)

#### Scenario: Region disappears on response
- **WHEN** the backend returns a successful recognition response
- **THEN** the pulsing region disappears
- **THEN** the returned annotations appear on the canvas

#### Scenario: Region disappears on error
- **WHEN** the backend returns an error during targeted recognition
- **THEN** the pulsing region disappears
- **THEN** an error message is shown to the user

### Requirement: Toolbar displays active recognition mode
The toolbar SHALL display a chip indicating the active recognition mode. The chip SHALL be hidden when in manual mode.

#### Scenario: Neume mode chip displayed
- **WHEN** neume recognition mode is active
- **THEN** toolbar shows a chip labeled "Neume mode (n)"

#### Scenario: Text mode chip displayed
- **WHEN** text recognition mode is active
- **THEN** toolbar shows a chip labeled "Text mode (t)"

#### Scenario: No chip in manual mode
- **WHEN** manual mode is active (no recognition mode)
- **THEN** no recognition mode chip is displayed in the toolbar

### Requirement: Detecting stage in SSE progress
The system SHALL handle the `detecting` SSE stage sent by the backend during neume recognition.

#### Scenario: Detecting stage received
- **WHEN** the backend sends an SSE event with `stage: "detecting"`
- **THEN** the system processes it as a valid progress event without error
