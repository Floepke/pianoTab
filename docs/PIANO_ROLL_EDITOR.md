# Vertical Piano Roll Editor

## Overview

The `PianoRollEditor` is a comprehensive vertical piano roll editor for the pianoTAB application. It displays MIDI data flowing from top to bottom with a piano keyboard on the left side for pitch reference.

## Features

### Visual Layout
- **Piano Keys Panel (Bottom)**: Interactive piano keyboard showing the black keys
- **Note Area (Main)**: Grid area where notes are displayed as rectangles
- **Vertical Time Flow**: Time progresses from top to bottom (like a waterfall)
- **Horizontal Pitch**: MIDI pitches from low (left) to high (right)

### Core Functionality

#### Data Integration
- Reads notes directly from the SCORE model
- Supports multiple staves with different events
- Uses the model's color inheritance system for note visualization
- Maintains real-time sync with the underlying data model

#### Visual Rendering
- **Notes**: Rendered as colored rectangles with position based on time and pitch
- **Piano Keys**: Visual keyboard with proper white/black key layout
- **Grid Lines**: Time grid (horizontal) and pitch grid (vertical)
- **Colors**: Supports hex colors from the model's property system

#### Interaction
- **Note Selection**: Click notes to select them
- **Piano Key Interaction**: Click piano keys for audio feedback or note insertion
- **Empty Area Clicks**: Can be used to add new notes at specific positions
- **Zoom Controls**: Time-based zoom in/out functionality
- **Scrolling**: Vertical scrolling through long compositions

### Technical Details

#### Coordinate System
- **X-axis**: Pitch (MIDI note 21-108, standard 88-key piano range)
- **Y-axis**: Time in beats (0 = top, increases downward)
- **Units**: All internal calculations in millimeters for precise rendering

#### Configuration
```python
# Piano roll dimensions
piano_keys_width_mm: float = 20.0    # Width of piano keyboard area
pixels_per_beat: float = 50.0         # Time scale resolution
zoom_factor: float = 1.0              # Time zoom multiplier

# Piano range (standard 88-key piano)
min_pitch: int = 21                   # A0
max_pitch: int = 108                  # C8
```

#### Color System
- Uses the model's inherited color properties
- Supports hex color codes (#RRGGBB)
- Fallback colors for missing color information
- Separate colors for left/right hand notes

## API Reference

### Constructor
```python
PianoRollEditor(editor_canvas: Canvas, score: Optional[SCORE] = None)
```

### Core Methods

#### Rendering
```python
render()                              # Render complete piano roll
_render_piano_keys()                  # Render piano keyboard
_render_grid()                        # Render time/pitch grid
_render_notes()                       # Render all notes from score
```

#### Interaction
```python
on_item_click(item_id, pos_mm)        # Handle canvas clicks
_select_note(note)                    # Select a note for editing
add_note_at_position(pitch, time)     # Add new note
delete_selected_notes()               # Remove selected notes
```

#### Navigation
```python
zoom_in(factor=1.2)                   # Zoom in on time axis
zoom_out(factor=1.2)                  # Zoom out on time axis
scroll_to_time(time)                  # Scroll to specific time
```

#### Coordinate Conversion
```python
get_time_at_y(y_mm)                   # Convert Y position to time
get_pitch_at_x(x_mm)                  # Convert X position to pitch
_pitch_to_x_mm(pitch)                 # Convert pitch to X coordinate
_time_to_y_mm(time)                   # Convert time to Y coordinate
```

## Usage Example

```python
from editor.editor import PianoRollEditor
from utils.canvas import Canvas
from file.SCORE import SCORE

# Create canvas and score
canvas = Canvas(width_mm=200, height_mm=150)
score = SCORE()
score.new_stave('treble', 4)

# Add some notes
score.new_note(stave_idx=0, time=0, pitch=60, duration=100)  # C4
score.new_note(stave_idx=0, time=100, pitch=64, duration=100)  # E4
score.new_note(stave_idx=0, time=512, pitch=67, duration=100)  # G4

# Create and render piano roll
piano_roll = PianoRollEditor(canvas, score)
piano_roll.render()

# Set up interaction
canvas.bind(on_item_click=lambda w, id, t, pos: piano_roll.on_item_click(id, pos))
```

## Integration with Main Application

The piano roll editor is designed to integrate seamlessly with the existing pianoTAB architecture:

- **Model Integration**: Direct connection to SCORE model
- **Canvas Compatibility**: Uses the existing Canvas widget system
- **Event System**: Compatible with Kivy event handling
- **Property Inheritance**: Leverages the model's sophisticated property system

## Future Enhancements

Potential improvements for the piano roll editor:

1. **Multi-track Support**: Visual separation of different staves
2. **Velocity Editing**: Visual velocity editing with note opacity/height
3. **Selection Rectangle**: Drag-to-select multiple notes
4. **Copy/Paste**: Note duplication and movement
5. **Quantization**: Snap-to-grid functionality
6. **Audio Playback**: Real-time audio preview
7. **MIDI Import/Export**: Direct MIDI file support
8. **Undo/Redo**: Edit history management