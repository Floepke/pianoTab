"""
Examples of using inherit_property() in different Event classes.

The inherit_property() function is universal and works for ALL Event classes!
"""
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from file.inherit_property import inherit_property
from typing import Optional, Literal, List


# ============================================================================
# Example 1: Simple inheritance - Note
# ============================================================================
@dataclass_json
@dataclass
class Note:
    id: int = 0
    pitch: int = 60
    hand: Literal['<', '>'] = '>'
    
    # Private fields (serialized)
    _color: Optional[str] = None
    _colorMidiNote: Optional[str] = None
    
    # Public properties (1 line each!)
    color = inherit_property('color', 'properties.globalNote.color', '#000000')
    
    # Custom resolver for hand-dependent color
    colorMidiNote = inherit_property(
        'colorMidiNote', None, '#000000',
        resolver=lambda self, score: (
            score.properties.globalNote.colorLeftMidiNote if self.hand == '<'
            else score.properties.globalNote.colorRightMidiNote
        )
    )


# ============================================================================
# Example 2: Grace Note
# ============================================================================
@dataclass_json
@dataclass
class GraceNote:
    id: int = 0
    pitch: int = 60
    
    _color: Optional[str] = None
    _visible: Optional[bool] = None
    
    # Inherit from globalGraceNote
    color = inherit_property('color', 'properties.globalGraceNote.color', '#000000')
    visible = inherit_property('visible', 'properties.globalGraceNote.visible', True)


# ============================================================================
# Example 3: Beam
# ============================================================================
@dataclass_json
@dataclass
class Beam:
    id: int = 0
    time: float = 0.0
    
    _color: Optional[str] = None
    _width: Optional[float] = None
    _slant: Optional[float] = None
    
    # All inherit from globalBeam
    color = inherit_property('color', 'properties.globalBeam.color', '#000000')
    width = inherit_property('width', 'properties.globalBeam.width', 4.0)
    slant = inherit_property('slant', 'properties.globalBeam.slant', 5.0)


# ============================================================================
# Example 4: Text
# ============================================================================
@dataclass_json
@dataclass
class Text:
    id: int = 0
    text: str = 'Text'
    
    _fontSize: Optional[int] = None
    _color: Optional[str] = None
    _family: Optional[str] = None
    
    # Inherit from globalText
    fontSize = inherit_property('fontSize', 'properties.globalText.fontSize', 12)
    color = inherit_property('color', 'properties.globalText.color', '#000000')
    family = inherit_property('family', 'properties.globalText.family', 'Courier New')


# ============================================================================
# Example 5: Slur with custom resolver
# ============================================================================
@dataclass_json
@dataclass
class Slur:
    id: int = 0
    type: Literal['above', 'below'] = 'above'
    
    _color: Optional[str] = None
    _middleWidth: Optional[float] = None
    
    color = inherit_property('color', 'properties.globalSlur.color', '#000000')
    middleWidth = inherit_property('middleWidth', 'properties.globalSlur.middleWidth', 1.0)


# ============================================================================
# Example 6: Articulation
# ============================================================================
@dataclass_json
@dataclass
class Articulation:
    type: str = 'staccato'
    xOffset: float = 0.0
    yOffset: float = 0.0
    
    _color: Optional[str] = None
    
    color = inherit_property('color', 'properties.globalArticulation.color', '#000000')


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def usage_examples():
    """Show how to use the properties."""
    from file.SCORE import SCORE
    
    score = SCORE()
    
    # Create a note
    note = score.new_note(pitch=60)
    
    # Need to attach score reference for auto-resolution
    note._score = score
    
    # Now you can use properties directly!
    print(note.color)  # Auto-resolves from globalNote.color
    
    note.color = '#FF0000'  # Set explicit
    print(note.color)  # '#FF0000'
    
    note.color = None  # Reset to inherit
    print(note.color)  # Back to globalNote.color
    
    # Change global property
    score.properties.globalNote.color = '#00FF00'
    print(note.color)  # '#00FF00' (inherits new value)
    
    # Works for all properties!
    note.colorMidiNote = '#0000FF'
    note.blackNoteDirection = '^'
    
    # Same pattern works for ALL Event classes:
    beam = score.new_beam()
    beam._score = score
    beam.color  # Auto-resolves from globalBeam.color
    beam.width  # Auto-resolves from globalBeam.width


# ============================================================================
# PATTERN SUMMARY
# ============================================================================
"""
For ANY Event class:

1. Add private backing fields:
   _color: Optional[str] = None
   _width: Optional[float] = None

2. Add public properties (1 line each!):
   color = inherit_property('color', 'properties.globalX.color', '#000000')
   width = inherit_property('width', 'properties.globalX.width', 1.0)

3. For complex logic, use resolver:
   prop = inherit_property('prop', None, default, resolver=lambda self, score: ...)

That's it! No repeated code, clean and simple! ✨
"""
