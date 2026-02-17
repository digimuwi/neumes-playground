## ADDED Requirements

### Requirement: Apostropha neume type available

The system SHALL include `apostropha` as a selectable neume type in the neume type dropdown.

#### Scenario: User selects apostropha
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Apostropha" appears as a selectable option

#### Scenario: Apostropha persists in state
- **WHEN** user selects "Apostropha" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'apostropha'`

### Requirement: Episema variants available for specific neumes

The system SHALL include episema variants as selectable neume types for: virga, clivis, climacus, and apostropha.

#### Scenario: User selects virga episema
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Virga episema" appears as a selectable option

#### Scenario: User selects clivis episema
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Clivis episema" appears as a selectable option

#### Scenario: User selects climacus episema
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Climacus episema" appears as a selectable option

#### Scenario: User selects apostropha episema
- **WHEN** user creates a neume annotation and opens the type dropdown
- **THEN** "Apostropha episema" appears as a selectable option

### Requirement: Episema types stored with space-separated naming

The system SHALL store episema neume types using space-separated lowercase naming convention.

#### Scenario: Virga episema storage format
- **WHEN** user selects "Virga episema" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'virga episema'`

#### Scenario: Clivis episema storage format
- **WHEN** user selects "Clivis episema" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'clivis episema'`

#### Scenario: Climacus episema storage format
- **WHEN** user selects "Climacus episema" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'climacus episema'`

#### Scenario: Apostropha episema storage format
- **WHEN** user selects "Apostropha episema" for a neume annotation
- **THEN** the annotation's `neumeType` is stored as `'apostropha episema'`

### Requirement: Episema types have descriptions

The system SHALL display descriptions for episema neume types that indicate the base neume with episema.

#### Scenario: Virga episema description
- **WHEN** user views the neume type options
- **THEN** "Virga episema" has a description indicating it is a single note with stem, with episema

#### Scenario: Clivis episema description
- **WHEN** user views the neume type options
- **THEN** "Clivis episema" has a description indicating it is two notes descending, with episema

#### Scenario: Climacus episema description
- **WHEN** user views the neume type options
- **THEN** "Climacus episema" has a description indicating it is three+ notes descending, with episema

#### Scenario: Apostropha episema description
- **WHEN** user views the neume type options
- **THEN** "Apostropha episema" has a description indicating it is a liquescent note, with episema
