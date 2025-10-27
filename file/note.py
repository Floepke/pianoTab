from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from file.articulation import Articulation
from typing import List, TYPE_CHECKING, Literal, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Note:
    """
    Musical note event with automatic property inheritance.
    
    Set values naturally:
        note.color = '#AAAAAA'  # Explicit color
        note.color = None       # Inherit from globalNote.color
    
    Access values directly:
        actual_color = note.color  # Auto-resolves inheritance
    """
    id: int = 0
    time: float = 0.0
    duration: float = 256.0
    pitch: int = 40
    velocity: int = 80
    articulation: List[Articulation] = field(default_factory=list)
    hand: Literal['<', '>'] = '>'
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    _colorMidiNote: Optional[str] = field(default=None, metadata=config(field_name='colorMidiNote'))
    _blackNoteDirection: Optional[Literal['^', 'v']] = field(default=None, metadata=config(field_name='blackNoteDirection'))
    
    def __post_init__(self):
        """Initialize score reference as a non-dataclass attribute."""
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        """Get color - inherits from globalNote.color if None."""
        if self._color is not None:
            return self._color
        if self.score is None:
            print("Warning: Note has no score reference for property inheritance.")
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalNote.color
    
    @color.setter
    def color(self, value: Optional[str]):
        """Set color - use None to reset to inheritance."""
        self._color = value
    
    # Property: colorMidiNote (hand-dependent inheritance)
    @property
    def colorMidiNote(self) -> str:
        """Get MIDI note color - inherits based on hand (left '<' or right '>')."""
        if self._colorMidiNote is not None:
            return self._colorMidiNote
        if self.score is None:
            return '#000000'  # Fallback if no score reference
        if self.hand == '<':
            return self.score.properties.globalNote.colorLeftMidiNote
        else:
            return self.score.properties.globalNote.colorRightMidiNote
    
    @colorMidiNote.setter
    def colorMidiNote(self, value: Optional[str]):
        """Set MIDI note color - use None to reset to inheritance."""
        self._colorMidiNote = value
    
    # Property: blackNoteDirection
    @property
    def blackNoteDirection(self) -> Literal['^', 'v']:
        """Get black note direction - inherits from globalNote.blackNoteDirection if None."""
        if self._blackNoteDirection is not None:
            return self._blackNoteDirection
        if self.score is None:
            return 'v'  # Fallback if no score reference
        return self.score.properties.globalNote.blackNoteDirection
    
    @blackNoteDirection.setter
    def blackNoteDirection(self, value: Optional[Literal['^', 'v']]):
        """Set black note direction - use None to reset to inheritance."""
        self._blackNoteDirection = value
