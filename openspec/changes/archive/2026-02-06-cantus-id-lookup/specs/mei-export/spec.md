## MODIFIED Requirements

### Requirement: MEI document structure

The exported MEI document SHALL follow the standard MEI hierarchy with meiHead, facsimile, and musical content sections.

#### Scenario: Valid MEI structure
- **WHEN** user exports annotations
- **THEN** the output SHALL contain:
  - XML declaration with UTF-8 encoding
  - `<mei>` root element with MEI namespace
  - `<meiHead>` with basic metadata
  - `<music>` containing `<facsimile>` and `<body>`
  - `<body>` containing `<mdiv>/<score>/<section>/<staff>/<layer>` hierarchy

#### Scenario: Cantus metadata included when present
- **WHEN** user exports annotations and document has Cantus metadata (cantusId, genre)
- **THEN** the `<meiHead>` SHALL contain a `<workList>` with the Cantus identifier and genre

#### Scenario: WorkList structure with Cantus metadata
- **WHEN** document has cantusId "006847" and genre "Antiphon"
- **THEN** the `<meiHead>` contains:
  ```xml
  <workList>
    <work>
      <identifier type="cantus">006847</identifier>
      <classification>
        <term type="genre">Antiphon</term>
      </classification>
    </work>
  </workList>
  ```

#### Scenario: No workList when no Cantus metadata
- **WHEN** user exports annotations and document has no Cantus metadata
- **THEN** the `<meiHead>` SHALL NOT contain a `<workList>` element
