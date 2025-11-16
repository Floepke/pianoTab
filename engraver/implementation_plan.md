# Engraver Implementation Plan

Based on the old Qt engraver (`engraver.py`, `engraver_helpers.py`) and the new SCORE model, here's what needs to be implemented:

## 1. Data Structures (DONE)
- ✅ LayoutData dataclass with DOC structure
- ✅ DOC is [page][line][event] hierarchy
- ✅ Events are dicts with type, time, and event-specific fields

## 2. Layout Calculation (_calculate_layout) - IN PROGRESS

### Step 1: Generate Structural Events
- Create barlines from SCORE.baseGrid
  - Each baseGrid has numerator/denominator/measureAmount
  - Calculate measure_length = numerator * (QUARTER_PIANOTICK * 4) / denominator
  - Create barline events at each measure boundary
  - Create gridline events at grid subdivisions
  - Create timesignature events

### Step 2: Process Notes
- For each note in SCORE.stave[].event.note:
  - Split notes that cross barlines
  - Original note becomes 'note'
  - Continuation parts become 'notesplit'
  - Add continuation_dot events at barline crossing points

### Step 3: Add Decorations
- Continuation dots: when a note is still sounding at a time point
- Stop signs: when all notes stop (rest point)
- Connect stems: when notes start at same time

### Step 4: Process Beams
- Add beam events from SCORE.stave[].event.beam

### Step 5: Add Other Events
- Slurs, text, tempo, grace notes, count lines, sections, repeats

### Step 6: Sort by Time
- Sort all events by time

### Step 7: Split into Lines
- Based on SCORE.lineBreak positions
- Each lineBreak marks start of new line

### Step 8: Calculate Staff Dimensions
- For each line, find pitch range
- Calculate staff width based on range

### Step 9: Organize into Pages
- Pack lines into pages based on page width
- Track leftover space for centering

### Step 10: Store in LayoutData
- Save DOC, staff_dimensions, staff_ranges, etc.

## 3. Drawing Operations (_prepare_*_operations) - TODO

Each _prepare method returns list of draw operations with:
- 'type': 'rect'|'line'|'text'|'ellipse'
- Coordinates in mm
- Colors, sizes, tags

### Drawing Methods Needed:
1. _prepare_page_operations: background rectangles
2. _prepare_barline_operations: vertical lines at measure boundaries
3. _prepare_gridline_operations: lighter vertical grid lines
4. _prepare_timesignature_operations: fraction text (4/4, 3/4, etc.)
5. _prepare_staff_operations: horizontal staff lines (keyboard layout)
6. _prepare_note_operations: filled rectangles for note duration
7. _prepare_notesplit_operations: continuation of split notes
8. _prepare_stem_operations: vertical lines connecting note start to keyboard
9. _prepare_beam_operations: thick lines connecting grouped notes
10. _prepare_slur_operations: curved lines (can use multiple line segments)
11. _prepare_text_operations: annotations, lyrics
12. _prepare_tempo_operations: tempo markings
13. _prepare_decoration_operations: continuation dots, stop signs, etc.

## 4. Constants Needed
- FRACTION = small time offset (0.01)
- PIANOTICK_QUARTER = 256.0
- Page dimensions from SCORE.properties
- Staff dimensions from SCORE.properties
- Draw scale factors

## 5. Helper Functions Needed
- pitch_to_x(pitch) → x coordinate in mm
- time_to_y(time) → y coordinate in mm
- calculate_staff_width(min_pitch, max_pitch) → width in mm
- range_staffs(line) → [(min_pitch, max_pitch)] for each staff
