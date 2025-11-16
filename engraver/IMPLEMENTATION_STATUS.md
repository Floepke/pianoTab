# Engraver Implementation Status

## Current Status
The engraver has been set up with:
- ✅ Threading architecture (background worker + main thread drawing)
- ✅ Task queue system (only newest task processes)
- ✅ Basic DOC structure generation (barlines, gridlines, time signatures)
- ✅ Test visualization working (red square + text + barlines on print preview)
- ✅ Safety checks (score None handling)
- ✅ Helper functions created (engraver_helpers_new.py)

## Next Implementation Steps

### Phase 1: Complete Layout Calculation (_calculate_layout)
Based on Qt engraver pre_calculate() function:

1. **Generate Structural Events** ✅ DONE
   - Barlines from baseGrid ✅
   - Gridlines from baseGrid.gridTimes ✅
   - Time signatures ✅
   - End barline ✅

2. **Process Notes** ⚠️ TODO
   - Convert SCORE.stave[].event.note to dict format
   - Call note_processor() to split notes on barlines
   - Add all note events to DOC

3. **Add Decorations** ⚠️ TODO
   - Call continuation_dot_stopsign_and_connectstem_processor()
   - Adds continuation dots, stop signs, connect stems

4. **Process Beams** ⚠️ TODO
   - Convert SCORE.stave[].event.beam
   - Implement beam_processor() or auto-grouping
   - Add beam events to DOC

5. **Add Other Events** ⚠️ TODO
   - Slurs, text, tempo, grace notes, count lines
   - Sections, repeats, etc.

6. **Sort Events** ✅ EASY
   - Sort all events by time

7. **Split into Lines** ⚠️ TODO
   - Based on SCORE.lineBreak positions
   - Create list of (start_time, end_time) tuples
   - Split events into lines

8. **Calculate Staff Dimensions** ⚠️ TODO
   - For each line, find pitch range per staff
   - Call calculate_staff_width() for each staff
   - Store margins from lineBreak

9. **Organize into Pages** ⚠️ TODO
   - Based on page_width from SCORE.properties
   - Pack lines horizontally until page full
   - Track leftover space for distribution

10. **Store in LayoutData** ⚠️ TODO
    - Return complete LayoutData with DOC

### Phase 2: Implement Drawing Operations

Each _prepare_*_operations() method needs to:
- Iterate through layout_data.DOC
- Calculate coordinates using helper functions
- Return list of drawing callables

Priority order (most visible first):
1. **_prepare_staff_operations** - Staff lines (keyboard layout)
2. **_prepare_barline_operations** - Vertical measure lines
3. **_prepare_note_operations** - Main note rectangles
4. **_prepare_stem_operations** - Stems connecting notes
5. **_prepare_gridline_operations** - Lighter grid lines
6. **_prepare_time_signature_operations** - 4/4, 3/4, etc.
7. **_prepare_beam_operations** - Beaming notation
8. **_prepare_decoration_operations** - Dots, stop signs
9. **_prepare_slur_operations** - Curved lines
10. **_prepare_text_operations** - Annotations
11. **_prepare_header_operations** - Title, composer
12. **_prepare_footer_operations** - Page numbers, copyright

### Phase 3: Testing & Refinement
- Test with simple scores (few notes)
- Test with complex scores (many measures)
- Performance tuning
- Visual refinement

## Current Test Visualization
The test drawing shows:
- Red rectangle (proves colors work)
- Text showing pages/lines/events (proves text works)
- Vertical barlines (proves line drawing works)
- Only draws on print preview (not editor)

## Key Differences from Qt Engraver

| Qt Engraver | New Engraver |
|-------------|--------------|
| `io['score']['events']['note']` | `SCORE.stave[].event.note` |
| `io['score']['events']['grid']` | `SCORE.baseGrid` |
| `io['score']['events']['linebreak']` | `SCORE.lineBreak` |
| `io['view'].new_line()` | `canvas.add_line()` |
| `io['view'].new_rectangle()` | `canvas.add_rectangle()` |
| `io['view'].new_text()` | `canvas.add_text()` |
| Dict-based events | Dataclass-based SCORE |
| Single-threaded | Multi-threaded |
| Qt Graphics Scene | Kivy Canvas |

## Helper Functions Available
In `engraver_helpers_new.py`:
- `calculate_staff_width()` - Calculate staff width from pitch range
- `trim_key_to_outer_sides_staff()` - Normalize key range
- `pitch2x_view()` - Convert pitch to x coordinate
- `tick2y_view()` - Convert time to y coordinate
- `note_processor()` - Split notes on barlines
- `continuation_dot_stopsign_and_connectstem_processor()` - Add decorations
- `continuation_dot()`, `stop_sign()` - Create decoration events
- `EQUALS()`, `GREATER()` - Float comparison helpers

## Next Immediate Action
Implement `_process_notes()` method to convert SCORE notes to dict format and process them.
