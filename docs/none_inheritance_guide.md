# None-Based Inheritance System

## Overview

The PianoTab model now uses **`None`** as the inheritance marker instead of `'*'`. This provides a more intuitive and Pythonic API.

## Usage

### Setting Properties

```python
score = SCORE()

# Create note with default inheritance (None)
note = score.new_note(pitch=60, time=0.0)
print(note.color)  # None (will inherit)

# Set explicit color
note.color = '#AAAAAA'
print(note.color)  # '#AAAAAA'

# Reset to inheritance
note.color = None
print(note.color)  # None (will inherit again)
```

### Getting Resolved Values

```python
# Get the actual color (resolving inheritance)
actual_color = note.get_color(score)
# If note.color is None, returns score.properties.globalNote.color
# If note.color is set, returns note.color

# Change global property
score.properties.globalNote.color = '#FF0000'
actual_color = note.get_color(score)  # '#FF0000' if note.color is None
```

## Migration from `'*'` to `None`

### Old System (using `'*'`)
```python
# Old way
note = score.new_note(color='*')  # Inherit
note.color = '#FF0000'  # Explicit
note.color = '*'  # Back to inherit
```

### New System (using `None`)
```python
# New way - more Pythonic!
note = score.new_note(color=None)  # Inherit (default)
note.color = '#AAAAAA'  # Explicit
note.color = None  # Back to inherit
```

## How It Works

### Model Definition

```python
@dataclass_json
@dataclass
class Note:
    # ... other fields ...
    
    # None means "inherit from globalProperties"
    color: Optional[str] = None
    colorMidiNote: Optional[str] = None
    blackNoteDirection: Optional[Literal['^', 'v']] = None
    
    def get_color(self, score: 'SCORE' = None) -> str:
        '''Get actual color, resolving inheritance.'''
        if self.color is not None:
            return self.color
        if score:
            return score.properties.globalNote.color
        return '#000000'  # Fallback
```

### Inheritance Paths

| Field | Inherits From |
|-------|---------------|
| `note.color` | `score.properties.globalNote.color` |
| `note.colorMidiNote` | `score.properties.globalNote.colorLeftMidiNote` or `colorRightMidiNote` |
| `note.blackNoteDirection` | `score.properties.globalNote.blackNoteDirection` |

## Benefits

1. **More Pythonic**: `None` is the standard Python way to indicate "no value"
2. **Type-safe**: `Optional[str]` is clearer than `Union[Literal['*'], str]`
3. **Intuitive**: `note.color = None` reads naturally as "reset to default"
4. **JSON-friendly**: `null` in JSON maps perfectly to `None`
5. **Compatible**: Works seamlessly with dataclasses-json serialization

## JSON Serialization

```python
# Create note with inherited color
note = score.new_note(color=None)

# Save to JSON
score.save('score.json')
# JSON: {"note": {"color": null, ...}}

# Load from JSON
loaded = SCORE.load('score.json')
# loaded.stave[0].event.note[0].color == None ✓
```

## Backwards Compatibility

If you have old `.pianotab` files using `'*'`, you can convert them:

```python
def migrate_star_to_none(score: SCORE):
    """Convert old '*' markers to None."""
    for stave in score.stave:
        for note in stave.event.note:
            if note.color == '*':
                note.color = None
            if note.colorMidiNote == '*':
                note.colorMidiNote = None
            if note.blackNoteDirection == '*':
                note.blackNoteDirection = None
        # ... same for other event types ...
```

## Complete Example

```python
from file.SCORE import SCORE

# Create score
score = SCORE()

# Set global colors
score.properties.globalNote.color = '#FF0000'  # Red
score.properties.globalNote.colorLeftMidiNote = '#0000FF'  # Blue
score.properties.globalNote.colorRightMidiNote = '#00FF00'  # Green

# Create notes with inheritance
note1 = score.new_note(pitch=60, hand='<')  # Inherits
note2 = score.new_note(pitch=64, hand='>')  # Inherits
note3 = score.new_note(pitch=67, color='#FFFF00')  # Yellow (explicit)

# Get resolved colors
print(note1.get_color(score))  # '#FF0000' (from globalNote.color)
print(note2.get_color(score))  # '#FF0000' (from globalNote.color)
print(note3.get_color(score))  # '#FFFF00' (explicit)

# Get MIDI colors (hand-dependent)
print(note1.get_colorMidiNote(score))  # '#0000FF' (left hand)
print(note2.get_colorMidiNote(score))  # '#00FF00' (right hand)

# Modify a note
note1.color = '#AA00AA'  # Override to purple
print(note1.get_color(score))  # '#AA00AA'

# Reset to inheritance
note1.color = None
print(note1.get_color(score))  # '#FF0000' (back to global)

# Save and load
score.save('example.json')
loaded = SCORE.load('example.json')
# All inheritance relationships preserved!
```

## Testing

Run the test suite:
```bash
python3 tests/test_none_inheritance.py
```

Expected output:
```
=== Test 1: Default inheritance (None) ===
note1.color = None (should be None - inheriting)
note1.get_color(score) = #FF0000 (should be #FF0000)
...
✅ All tests passed!
```
