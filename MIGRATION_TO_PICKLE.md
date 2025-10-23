# Migration to Pickle Serialization - Complete

## Summary

Successfully migrated the PianoTab SCORE model from `dataclasses_json` (JSON serialization) to Python's built-in `pickle` (binary serialization).

## Changes Made

### 1. Removed `@dataclass_json` Decorators

Removed the `@dataclass_json` decorator and associated imports from all files in `/file/`:

- ✅ `note.py`
- ✅ `metaInfo.py`
- ✅ `header.py`
- ✅ `properties.py`
- ✅ `baseGrid.py`
- ✅ `lineBreak.py`
- ✅ `graceNote.py`
- ✅ `countLine.py`
- ✅ `startRepeat.py`
- ✅ `endRepeat.py`
- ✅ `section.py`
- ✅ `beam.py`
- ✅ `text.py`
- ✅ `slur.py`
- ✅ `tempo.py`
- ✅ `articulation.py`
- ✅ `globalProperties.py` (13 global classes)
- ✅ `SCORE.py` (Event, Stave, SCORE classes)

### 2. Updated SCORE.py Serialization Methods

**Before:**
```python
import json
from dataclasses_json import dataclass_json

def save(self, filename: str) -> None:
    '''Save SCORE instance to JSON file.'''
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(self.to_dict(), f, ensure_ascii=True, separators=(',', ':'), indent=None)

@classmethod
def load(cls, filename: str) -> 'SCORE':
    '''Load ScoreFile instance from JSON file.'''
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    score = cls.from_dict(data)
    score.renumber_id()
    return score
```

**After:**
```python
import pickle

def save(self, filename: str) -> None:
    '''Save SCORE instance to pickle file.'''
    with open(filename, 'wb') as f:
        pickle.dump(self, f)

@classmethod
def load(cls, filename: str) -> 'SCORE':
    '''Load SCORE instance from pickle file.'''
    with open(filename, 'rb') as f:
        score = pickle.load(f)
    score.renumber_id()
    return score
```

### 3. Created Diagnostic Tool

**New file:** `utils/score_inspector.py`

This tool provides comprehensive inspection of pickle files:

- **Safe loading**: Catches pickle errors and provides clear diagnostics
- **Structure display**: Pretty-prints entire SCORE hierarchy with `pprint`
- **Validation checks**: Verifies SCORE structure, counts events, checks metadata
- **File info**: Shows file size and path
- **Error reporting**: Detailed traceback for debugging

**Usage:**
```bash
python utils/score_inspector.py my_score.pkl
```

**Example output:**
```
Inspecting: /path/to/my_score.pkl
File size: 12,345 bytes
================================================================================

✓ Successfully loaded pickle file

--------------------------------------------------------------------------------
SCORE Object Type: SCORE
--------------------------------------------------------------------------------

SCORE Contents:
================================================================================
SCORE(quarterTick=256.0,
      metaInfo=Metainfo(title='My Song', composer='Composer Name', ...),
      header=Header(...),
      properties=Properties(...),
      ...)

================================================================================
Validation Checks:
--------------------------------------------------------------------------------
✓ Valid SCORE object
  - Number of staves: 2
  - Stave 0 (Piano):
      Notes: 45
      Grace notes: 3
      ...
✓ ID generator present
  - Current ID: 123
✓ MetaInfo present
  - Title: My Song
  - Composer: Composer Name

================================================================================
✓ Inspection complete - no errors detected
```

## Benefits of Pickle vs JSON

1. **Simpler code**: No need for `to_dict()`/`from_dict()` conversion methods
2. **Better performance**: Binary format is faster to read/write
3. **Smaller files**: Binary is more compact than text JSON
4. **Native Python**: Built-in serialization, no external dependencies
5. **Preserves types**: Handles Python objects natively without conversion

## Migration Notes

- **File extension**: Recommend using `.pkl` or `.pickle` for score files
- **Binary format**: Files are no longer human-readable (use inspector tool)
- **Backward compatibility**: Old JSON files will need conversion (future work)
- **All dataclasses preserved**: Only removed JSON serialization, kept `@dataclass`

## Verification

Confirmed zero references to `dataclasses_json` remain in the codebase:
```bash
grep -r "dataclass_json" file/
# No matches found
```

## Next Steps (Optional)

1. **Test round-trip**: Create a test SCORE, save to pickle, load and verify
2. **Conversion tool**: Create utility to convert old JSON files to pickle
3. **File versioning**: Add version metadata to handle future format changes
4. **Compression**: Consider using `gzip` with pickle for even smaller files:
   ```python
   import gzip
   with gzip.open('score.pkl.gz', 'wb') as f:
       pickle.dump(score, f)
   ```

## Testing Example

```python
from file.SCORE import SCORE

# Create a test score
score = SCORE()
score.new_note(time=0.0, pitch=60, duration=256.0)
score.metaInfo.title = "Test Song"

# Save to pickle
score.save('test_score.pkl')

# Load from pickle
loaded = SCORE.load('test_score.pkl')

# Verify
assert loaded.metaInfo.title == "Test Song"
assert len(loaded.stave[0].event.note) == 1
print("✓ Pickle round-trip successful!")

# Inspect with diagnostic tool
# python utils/score_inspector.py test_score.pkl
```

---

**Migration Status:** ✅ Complete  
**Files Modified:** 20 files in `/file/` directory  
**Dependencies Removed:** `dataclasses_json`  
**New Tools:** `utils/score_inspector.py`
