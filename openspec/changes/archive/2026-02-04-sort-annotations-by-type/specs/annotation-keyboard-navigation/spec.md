## MODIFIED Requirements

### Requirement: Reading order navigation

Annotations SHALL be ordered for navigation by their type first, then by their position on the page.

#### Scenario: Type takes priority over position

- **WHEN** a syllable annotation is below a neume annotation
- **THEN** the syllable still comes first in navigation order

#### Scenario: Syllables come before neumes

- **WHEN** annotations include both syllables and neumes
- **THEN** all syllables appear before all neumes in navigation order

#### Scenario: Reading order within type

- **WHEN** multiple annotations have the same type
- **THEN** they are ordered by reading order (top-to-bottom, left-to-right) within that type

#### Scenario: Top-to-bottom ordering within type

- **WHEN** two annotations of the same type are at different vertical positions
- **THEN** the annotation closer to the top comes first in navigation order

#### Scenario: Left-to-right for same row within type

- **WHEN** two annotations of the same type are at approximately the same vertical position
- **THEN** the annotation closer to the left comes first in navigation order

#### Scenario: Row threshold

- **WHEN** two annotations have vertical centers within 2% of the image height
- **THEN** they are considered to be on the same row for ordering purposes

#### Scenario: Unknown types sort last

- **WHEN** an annotation has a type not in the known priority list
- **THEN** it appears after all known types in navigation order
