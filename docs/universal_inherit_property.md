# Universal `inherit_property()` Pattern

## ✨ The Universal Solution - No Repeated Code!

The `inherit_property()` function in `/file/inherit_property.py` is a **universal, reusable solution** that works for ALL Event classes!

## How to Use in ANY Event Class

### Step 1: Define regular dataclass fields

```python
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from file.inherit_property import inherit_property
from typing import Optional

@dataclass_json
@dataclass
class YourEvent:
    id: int = 0
    time: float = 0.0
    
    # Regular fields - these serialize normally!
    color: Optional[str] = None
    width: Optional[float] = None
    visible: Optional[bool] = None
    
    def __post_init__(self):
        """Move values to private storage for property access."""
        object.__setattr__(self, '_inherit_color', self.color)
        object.__setattr__(self, '_inherit_width', self.width)
        object.__setattr__(self, '_inherit_visible', self.visible)

# Step 2: Enhance fields with inheritance (AFTER class definition)
YourEvent.color = inherit_property('color', 'properties.globalYourEvent.color', '#000000')
YourEvent.width = inherit_property('width', 'properties.globalYourEvent.width', 1.0)
YourEvent.visible = inherit_property('visible', 'properties.globalYourEvent.visible', True)
```

### That's it! Super clean! ✨

## Usage Examples

```python
# Create event
event = score.new_your_event()
event._score = score  # Attach score reference

# Use properties naturally
print(event.color)  # Auto-resolves from global if None
event.color = '#AAAAAA'  # Set explicit
event.color = None  # Reset to inherit

# JSON serialization works perfectly!
score.save('file.json')  # color field serializes normally
loaded = SCORE.load('file.json')  # Loads back correctly
```

## For Complex Logic (like hand-dependent colors)

```python
# Use custom resolver for conditional inheritance
Note.colorMidiNote = inherit_property(
    'colorMidiNote', 
    None,  # No simple path
    '#000000',
    resolver=lambda self, score: (
        score.properties.globalNote.colorLeftMidiNote if self.hand == '<'
        else score.properties.globalNote.colorRightMidiNote
    )
)
```

## Complete Pattern for All Event Classes

```python
# 1. Note
@dataclass_json
@dataclass  
class Note:
    color: Optional[str] = None
    colorMidiNote: Optional[str] = None
    
    def __post_init__(self):
        object.__setattr__(self, '_inherit_color', self.color)
        object.__setattr__(self, '_inherit_colorMidiNote', self.colorMidiNote)

Note.color = inherit_property('color', 'properties.globalNote.color', '#000000')
Note.colorMidiNote = inherit_property('colorMidiNote', ..., resolver=...)

# 2. Beam  
@dataclass_json
@dataclass
class Beam:
    color: Optional[str] = None
    width: Optional[float] = None
    
    def __post_init__(self):
        object.__setattr__(self, '_inherit_color', self.color)
        object.__setattr__(self, '_inherit_width', self.width)

Beam.color = inherit_property('color', 'properties.globalBeam.color', '#000000')
Beam.width = inherit_property('width', 'properties.globalBeam.width', 4.0)

# 3. Text
@dataclass_json
@dataclass
class Text:
    fontSize: Optional[int] = None
    color: Optional[str] = None
    
    def __post_init__(self):
        object.__setattr__(self, '_inherit_fontSize', self.fontSize)
        object.__setattr__(self, '_inherit_color', self.color)

Text.fontSize = inherit_property('fontSize', 'properties.globalText.fontSize', 12)
Text.color = inherit_property('color', 'properties.globalText.color', '#000000')

# Same pattern for ALL Event classes! 🎉
```

## Benefits

✅ **One universal solution** - no repeated code!
✅ **Clean syntax** - just 1-2 lines per property
✅ **Works with dataclasses-json** - fields serialize normally
✅ **Natural usage** - `note.color = '#AAA'` or `note.color = None`
✅ **Automatic resolution** - `note.color` auto-resolves when None
✅ **Flexible** - supports custom resolvers for complex logic
✅ **Maintainable** - all inheritance logic in one place

## The Magic

The `inherit_property()` function:
1. Creates a property that wraps the original field
2. Stores values in `_inherit_{field_name}` 
3. Auto-resolves from score path when value is None
4. Original field stays intact for JSON serialization

**Result**: You get automatic inheritance with minimal boilerplate! 🚀
