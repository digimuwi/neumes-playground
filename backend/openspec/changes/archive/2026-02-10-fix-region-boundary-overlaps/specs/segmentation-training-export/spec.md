## ADDED Requirements

### Requirement: Clip overlapping region boundaries at vertical midpoint
After constructing all TextRegion and MusicRegion boundaries, the system SHALL detect vertically overlapping adjacent region pairs and clip their boundaries at the vertical midpoint of the overlap zone. This ensures no pixel belongs to more than one region.

#### Scenario: TextRegion bottom overlaps MusicRegion top
- **WHEN** a TextRegion has Y_max=1178 and the adjacent MusicRegion below has Y_min=1136
- **THEN** the clip line is at Y=1157, the TextRegion boundary is clipped from below at Y=1157, and the MusicRegion boundary is clipped from above at Y=1157

#### Scenario: No overlap between regions
- **WHEN** a TextRegion's Y_max is less than or equal to the adjacent MusicRegion's Y_min
- **THEN** both boundaries are left unchanged

#### Scenario: Polygon clipping preserves shape
- **WHEN** a TextRegion boundary polygon is clipped at a horizontal Y threshold
- **THEN** vertices beyond the threshold are removed, edges crossing the threshold are interpolated to produce new vertices at Y=threshold, and the resulting polygon is closed

#### Scenario: TextLine Coords clipped to match TextRegion
- **WHEN** a TextRegion boundary is clipped
- **THEN** the enclosed TextLine Coords are clipped identically
