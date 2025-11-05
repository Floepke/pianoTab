# Adding a New Field to a Dataclass - Checklist

This guide explains how to add a new field to any dataclass in the pianoTAB project while maintaining the validation system.

## Overview

The validation system automatically reads field names and defaults from your dataclass metadata, so adding a field is straightforward. The key is using the `field()` function with proper `metadata=config(field_name='...')` for JSON field name mapping.

---

## Step-by-Step Process

### Example: Adding `accidental` field to `Note`

Let's say you want to add a new field `accidental` to the `Note` class that can be `'♯'`, `'♭'`, `'♮'`, or `None`.

---

### Step 1: Add the Field to the Dataclass

**File**: `file/note.py`

Choose whether the field should:
- **Have a JSON shortname** (appears in lists frequently) → Use `field(default=..., metadata=config(field_name='...'))`
- **Keep full name** (rare or descriptive) → Use simple assignment

```python
# Option A: With shortened JSON name (recommended for common fields)
accidental: Optional[str] = field(default=None, metadata=config(field_name='acc'))

# Option B: Without shortening (keeps 'accidental' in JSON)
accidental: Optional[str] = None
```

**Where to add it**: Add near the top with other regular fields, BEFORE the `_property` storage fields.

```python
@dataclass
class Note:
    id: int = 0
    time: float = 0.0
    duration: float = field(default=256.0, metadata=config(field_name='dur'))
    pitch: int = 40
    velocity: int = field(default=80, metadata=config(field_name='vel'))
    accidental: Optional[str] = field(default=None, metadata=config(field_name='acc'))  # ← NEW FIELD
    articulation: List[Articulation] = field(default_factory=list, metadata=config(field_name='art'))
    hand: Literal['<', '>'] = '>'
    
    # Storage fields for inherited properties...
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    # ...
```

**Important**: 
- Always provide a **default value** (or `default_factory` for lists/dicts)
- This default will be used when loading old JSON files that don't have this field

---

### Step 2: Update the Constructor Method (if exists)

**File**: `file/SCORE.py`

If there's a `new_note()` method or similar constructor, add the new parameter:

```python
def new_note(self,
             stave_idx: int = 0,
             time: float = 0.0,
             duration: float = 256.0,
             pitch: int = 40,
             velocity: int = 80,
             accidental: str = None,  # ← NEW PARAMETER
             articulation: List = [],
             hand: str = '>',
             color: str = None,
             colorMidiLeftNote: str = None,
             colorMidiRightNote: str = None,
             blackNoteDirection: str = None) -> Note:
    '''Add a note to the specified stave.'''
    
    note = Note(id=self._next_id(), 
                time=time, 
                duration=duration, 
                pitch=pitch, 
                velocity=velocity,
                accidental=accidental,  # ← PASS IT TO CONSTRUCTOR
                articulation=articulation, 
                hand=hand, 
                _color=color,
                _colorMidiLeftNote=colorMidiLeftNote,
                _colorMidiRightNote=colorMidiRightNote,
                _blackNoteDirection=blackNoteDirection)
    
    note.score = self
    self.get_stave(stave_idx).event.note.append(note)
    return note
```

---

### Step 3: Test It!

Create a simple test to verify everything works:

```python
#!/usr/bin/env python3
"""Test new accidental field."""

from file.SCORE import SCORE

# Create score with new field
s = SCORE()
s.new_note(pitch=60, accidental='♯')
s.new_note(pitch=62, accidental='♭')
s.new_note(pitch=64)  # No accidental (uses default None)

# Save
s.save('tests/test_accidental.pianoTAB')

# Load back
loaded = SCORE.load('tests/test_accidental.pianoTAB')

# Verify
assert loaded.stave[0].event.note[0].accidental == '♯'
assert loaded.stave[0].event.note[1].accidental == '♭'
assert loaded.stave[0].event.note[2].accidental == None

print("✓ New field works correctly!")
```

---

### Step 4: Test Backward Compatibility

Create a test that loads an OLD JSON file (without your new field):

```python
#!/usr/bin/env python3
"""Test loading old file without new field."""

from file.SCORE import SCORE
import json

# Create old-format JSON (without 'accidental' field)
old_data = {
    "stave": [{
        "event": {
            "note": [
                {"id": 1, "time": 0, "pitch": 60}  # No 'acc' field
            ]
        }
    }]
}

with open('tests/test_old_format.pianoTAB', 'w') as f:
    json.dump(old_data, f)

# Load it - validation should fill in default
loaded = SCORE.load('tests/test_old_format.pianoTAB')

# Verify default was applied
assert loaded.stave[0].event.note[0].accidental == None
print("✓ Backward compatibility works!")
```

The validation system will print:
```
⚠ Stave[0].note[0]: Missing field 'acc' (code: 'accidental'), using default: None
```

---

## What the Validation System Does Automatically

✅ **Detects the new field** from dataclass metadata  
✅ **Extracts the default value** (`None` in our example)  
✅ **Detects missing field** when loading old JSON  
✅ **Fills in the default** automatically  
✅ **Prints a warning** so you know what happened  

**You don't need to update `validation.py` manually!**

---

## For Inherited Properties (Advanced)

If you want the field to support **property inheritance** (like `color`, `fontSize`, etc.):

### Step 1: Add to GlobalNote (or relevant Global class)

**File**: `file/globalProperties.py`

```python
@dataclass
class GlobalNote:
    color: str = '#000000'
    # ... other fields ...
    accidentalColor: str = field(default='#FF0000', metadata=config(field_name='accCol'))  # NEW
```

### Step 2: Add storage field to Note

**File**: `file/note.py`

```python
# Storage fields for inherited properties
_color: Optional[str] = field(default=None, metadata=config(field_name='color'))
_accidentalColor: Optional[str] = field(default=None, metadata=config(field_name='accCol'))  # NEW
```

### Step 3: Add @property getter/setter

**File**: `file/note.py`

```python
# Property: accidentalColor
@property
def accidentalColor(self) -> str:
    """Get accidental color - inherits from globalNote.accidentalColor if None."""
    if self._accidentalColor is not None:
        return self._accidentalColor
    if self.score is None:
        print("Warning: Note has no score reference for property inheritance.")
        return '#FF0000'  # Fallback if no score reference
    return self.score.properties.globalNote.accidentalColor

@accidentalColor.setter
def accidentalColor(self, value: Optional[str]):
    """Set accidental color - use None to reset to inheritance."""
    self._accidentalColor = value
```

---

## Common Field Types

### Simple value with default
```python
myField: int = 42
myField: str = 'default'
myField: float = 1.0
```

### Optional (can be None)
```python
myField: Optional[str] = None
myField: Optional[int] = None
```

### List (use default_factory)
```python
myList: List[str] = field(default_factory=list)
myList: List[int] = field(default_factory=lambda: [1, 2, 3])
```

### With JSON shortening
```python
myLongFieldName: str = field(default='value', metadata=config(field_name='short'))
```

---

## Naming Guidelines for JSON Shortening

**Shorten if** (saves space, appears in lists):
- Length > 5 characters
- Appears many times (Note, Slur, etc.)
- Meaning is clear in context

**Keep full name if**:
- Already ≤ 5 characters (`pitch`, `time`, `hand`)
- Shortening loses meaning (`distFromSide`)
- Rarely used field
- Descriptive field names important for readability

**Examples**:
- `duration` → `dur` ✓ (common, clear)
- `velocity` → `vel` ✓ (common, clear)
- `x1_semitonesFromC4` → `x1` ✓ (huge savings, context clear)
- `distFromSide` → keep full ✓ (loses meaning)
- `pitch` → keep ✓ (already short)

---

## Troubleshooting

### "Missing field warning appears but I added the field!"

**Check**:
1. Did you use `field()` with `metadata=config(field_name='...')`?
2. Does the JSON name match what's in the file?
3. Did you restart Python after changing the code?

### "Old files fail to load"

**Solution**: Make sure your field has a default value:
```python
# Good - has default
myField: int = 0

# Bad - no default, required field
myField: int
```

### "Field appears in JSON with wrong name"

**Check** the `field_name` in metadata:
```python
myField: str = field(default='x', metadata=config(field_name='myFld'))
                                                                ^^^^^ This is what appears in JSON
```

---

## Summary Checklist

When adding a new field:

- [ ] Add field to dataclass with default value
- [ ] Add `metadata=config(field_name='...')` if shortening JSON name
- [ ] Update constructor method (e.g., `new_note()`) if exists
- [ ] Test: Create object with new field
- [ ] Test: Save and load with new field
- [ ] Test: Load old JSON without field (verify default fills in)
- [ ] (Optional) Add to GlobalXxx if using property inheritance
- [ ] (Optional) Add @property getter/setter for inheritance

**The validation system handles the rest automatically!** ✨
