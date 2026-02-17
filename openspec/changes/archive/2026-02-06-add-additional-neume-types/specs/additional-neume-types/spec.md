## ADDED Requirements

### Requirement: Cephalicus neume type available

The system SHALL include `cephalicus` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects cephalicus
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Cephalicus" appears as a selectable option with description "Liquescent descending neume"

### Requirement: Equaliter neume type available

The system SHALL include `equaliter` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects equaliter
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Equaliter" appears as a selectable option with description "Equal rhythmic value indication"

### Requirement: Inferius neume type available

The system SHALL include `inferius` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects inferius
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Inferius" appears as a selectable option with description "Lower pitch indication"

### Requirement: Levare neume type available

The system SHALL include `levare` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects levare
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Levare" appears as a selectable option with description "Upward melodic movement"

### Requirement: Mediocriter neume type available

The system SHALL include `mediocriter` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects mediocriter
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Mediocriter" appears as a selectable option with description "Moderate rhythmic value"

### Requirement: Pressionem neume type available

The system SHALL include `pressionem` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects pressionem
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Pressionem" appears as a selectable option with description "Pressure/emphasis marking"

### Requirement: Sursum neume type available

The system SHALL include `sursum` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects sursum
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Sursum" appears as a selectable option with description "Upward direction indicator"

### Requirement: New neume types stored with lowercase naming

The system SHALL store the new neume types using lowercase naming convention.

#### Scenario: Cephalicus storage format
- **WHEN** user selects "Cephalicus" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'cephalicus'`

#### Scenario: Equaliter storage format
- **WHEN** user selects "Equaliter" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'equaliter'`

#### Scenario: Inferius storage format
- **WHEN** user selects "Inferius" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'inferius'`

#### Scenario: Levare storage format
- **WHEN** user selects "Levare" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'levare'`

#### Scenario: Mediocriter storage format
- **WHEN** user selects "Mediocriter" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'mediocriter'`

#### Scenario: Pressionem storage format
- **WHEN** user selects "Pressionem" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'pressionem'`

#### Scenario: Sursum storage format
- **WHEN** user selects "Sursum" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'sursum'`
