## MODIFIED Requirements

### Requirement: Submit training data on click
When clicked, the Contribute button SHALL submit the current image and annotations to the backend `/contribute` endpoint, which saves the contribution and triggers training if thresholds are met.

#### Scenario: Successful contribution submission
- **WHEN** user clicks enabled Contribute button
- **THEN** system sends POST request to `/contribute` with image blob and transformed annotations
- **THEN** annotations are transformed: syllables grouped into lines with polygon boundaries, coordinates converted from normalized (0-1) to pixels
- **THEN** each line includes its `boundary` polygon (from stored OCR line boundaries or synthesized from syllable polygons)
- **THEN** each syllable includes its `boundary` polygon (denormalized to pixel coordinates)
- **THEN** neumes include `bbox: {x, y, width, height}` computed from their polygon bounding rect (denormalized to pixels)

#### Scenario: Contribution triggers training check
- **WHEN** backend saves contribution successfully
- **THEN** contribution count is incremented
- **THEN** training is triggered if count reaches threshold (10 for segmentation, 30 for recognition)
