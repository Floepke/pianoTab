# Auto-Save for Runtime Inspection

## Overview
The PianoTab SCORE class supports **auto-save** mode, which automatically writes the current score state to a file whenever changes are made. This is useful for inspecting the score structure during development and runtime debugging.

## Usage

### Enabling Auto-Save
```python
from file.SCORE import SCORE

score = SCORE()
score.enable_auto_save('current.pianotab')  # Default path
# Or specify a custom path:
# score.enable_auto_save('debug/my_score.pianotab')
```

### Disabling Auto-Save
```python
score.disable_auto_save()
```

## How It Works
- When enabled, `current.pianotab` is written **every time** you add an event (note, grace note, text, etc.)
- Changes trigger auto-save:
  - `score.new_note(...)`
  - `score.new_grace_note(...)`
  - `score.new_beam(...)`
  - `score.new_text(...)`
  - `score.new_slur(...)`
  - `score.new_tempo(...)`
  - `score.new_basegrid(...)`
  - `score.new_linebreak(...)`
  - And all other `new_*` methods

## Benefits
- **Real-time inspection**: Open `current.pianotab` in your editor to see the JSON structure as your app runs
- **Debugging**: Track exactly what's being written to the score model
- **No manual saves**: The file updates automatically on every change

## Performance Note
Auto-save writes to disk on every event addition. For production use with large scores, consider:
- Disabling auto-save in production
- Using auto-save only during development/debugging
- Implementing a throttled save (e.g., save every N events)

## Example Output
With auto-save enabled, `current.pianotab` always reflects the current state:

```json
{
  "quarterNoteLength": 256.0,
  "metaInfo": {...},
  "header": {...},
  "properties": {...},
  "stave": [
    {
      "name": "Stave 1",
      "scale": 1.0,
      "event": {
        "note": [
          {"id": 1, "pitch": 60, "dur": 256.0, "time": 0.0, ...},
          {"id": 2, "pitch": 62, "dur": 256.0, "time": 256.0, ...}
        ],
        ...
      }
    }
  ]
}
```

## In the App
The main PianoTab application enables auto-save by default:

```python
# In pianotab.py
self.score = SCORE()
self.score.enable_auto_save('current.pianotab')
```

This means `current.pianotab` is always up-to-date while the app is running!
