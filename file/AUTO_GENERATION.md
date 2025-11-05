# Auto-Generation System - Quick Reference

## Overview

The pianoTAB project now uses **auto-generation** for all `new_*()` methods in `SCORE.py`. 

**You only edit ONE place to add a field**: the Event dataclass itself.

## Key Benefit

**Before (manual):** Field names defined in 3 places
- Event dataclass definition
- SCORE.new_*() parameter list  
- SCORE.new_*() constructor call

**After (auto-generated):** Field names defined in 1 place
- Event dataclass definition ✅

## How It Works

1. Event classes define fields with metadata:
```python
duration: float = field(default=256.0, metadata=config(field_name='dur'))
```

2. `file/event_factory.py` uses `dataclasses.fields()` to introspect

3. `setup_event_factories(SCORE)` generates all `new_*()` methods at module load

4. Methods accept `stave_idx=0` and `**kwargs` for all fields

5. Handles underscore fields automatically (`_color` → accepts `color` parameter)

## Adding a New Field - One Step

Edit the Event class (e.g., `file/note.py`):

```python
@dataclass_json
@dataclass
class Note:
    # ... existing fields ...
    
    # Add your new field here - DONE!
    myNewField: str = field(default='defaultValue', metadata=config(field_name='newFld'))
```

That's it! No need to edit `SCORE.py`.

## Usage

```python
score = SCORE()

# Auto-generated method accepts your field
note = score.new_note(pitch=60, myNewField='custom')

# Also accepts underscore field names
note = score.new_note(pitch=60, _color='#FF0000')  # Both _color and color work
```

## Auto-Generated Methods

All these methods are auto-generated:
- `new_note`
- `new_grace_note`
- `new_beam`
- `new_text`
- `new_slur`
- `new_count_line`
- `new_section`
- `new_start_repeat`
- `new_end_repeat`
- `new_tempo`

## Trade-Off

**Lost:** IDE parameter hints (no autocomplete for field names)

**Gained:** 
- Eliminate 66% code duplication
- Single source of truth for field definitions
- Easier maintenance as project grows
- Less chance of parameter/field name mismatches

## Files

- `file/event_factory.py` - Auto-generation logic
- `file/SCORE.py` - Imports and calls `setup_event_factories(SCORE)`
- All Event classes (note.py, text.py, etc.) - Field definitions

## See Also

- `file/ADDING_FIELDS.md` - Comprehensive field addition guide
- `file/validation.py` - Validation system documentation
