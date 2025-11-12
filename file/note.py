from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from file.articulation import Articulation
from typing import List, TYPE_CHECKING, Literal, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Note:
    '''Musical note event with automatic property inheritance.'''
    
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique note identifier',
            'tree_editable': False,  # IDs shouldn't be edited
            'tree_edit_type': 'readonly',
        }
    )
    
    time: float = field(
        default=0.0,
        metadata={
            **config(field_name='time'),
            'tree_icon': 'property',
            'tree_tooltip': 'Start time in time units',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    
    duration: float = field(
        default=256.0,
        metadata={
            **config(field_name='duration'),
            'tree_icon': 'property',
            'tree_tooltip': 'Note duration in time units',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 1.0,
                'step': 1.0,
            }
        }
    )
    
    pitch: int = field(
        default=40,
        metadata={
            'tree_icon': 'accidental',
            'tree_tooltip': 'MIDI pitch (36=C2, 60=C4, 84=C6)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 0,
                'max': 127,
                'step': 1,
            }
        }
    )
    
    velocity: int = field(
        default=80,
        metadata={
            **config(field_name='velocity'),
            'tree_icon': 'property',
            'tree_tooltip': 'Note velocity/dynamics (0-127, only affects MIDI playback)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 0,
                'max': 127,
                'step': 1,
            }
        }
    )
    
    articulation: List[Articulation] = field(
        default_factory=list,
        metadata={
            **config(field_name='art'),
            'tree_icon': 'property',
            'tree_tooltip': 'List of articulations applied to this note',
            'tree_edit_type': 'list',  # Expandable list in tree
        }
    )
    
    hand: Literal['<', '>'] = field(
        default='>',
        metadata={
            **config(field_name='hand'),
            'tree_icon': 'property',
            'tree_tooltip': 'Hand assignment: < = left hand, > = right hand',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['<', '>'],
                'choice_labels': ['Left Hand', 'Right Hand'],
                'choice_icons': ['noteLeft', 'noteRight'],
            }
        }
    )
    
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Color of the note head (None = inherit from globalNote)',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,  # Can be set to None for inheritance
            }
        }
    )
    
    _colorMidiLeftNote: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='colorMidiLeftNote'),
            'tree_icon': 'colorproperty',
            'tree_label': 'MIDI Color (Left)',  # Override display name
            'tree_tooltip': 'Color of MIDI rectangle for left hand notes',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    
    _colorMidiRightNote: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='colorMidiRightNote'),
            'tree_icon': 'colorproperty',
            'tree_label': 'MIDI Color (Right)',  # Override display name
            'tree_tooltip': 'Color of MIDI rectangle for right hand notes',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    
    _blackNoteDirection: Optional[Literal['^', 'v']] = field(
        default=None,
        metadata={
            **config(field_name='blackNoteDirection'),
            'tree_icon': 'property',
            'tree_tooltip': 'Stem direction for black notes',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['^', 'v', None],
                'choice_labels': ['Up', 'Down', 'Inherit'],
                'choice_icons': ['blacknoteup', 'blacknotedown', 'previous'],
            }
        }
    )
    
    _stemLengthMm: Optional[float] = field(
        default=None,
        metadata={
            **config(field_name='stemLengthMm'),
            'tree_icon': 'property',
            'tree_tooltip': 'Length of note stem in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 50.0,
                'step': 0.5,
                'allow_none': True,  # None = inherit
            }
        }
    )

    def __post_init__(self):
        '''Initialize score reference as a non-dataclass attribute.'''
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        '''Get color - inherits from globalNote.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: Note has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalNote.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
    
    # Property: colorMidiLeftNote
    @property
    def colorMidiLeftNote(self) -> str:
        '''Get left MIDI note color - inherits from globalNote.colorLeftMidiNote if None.'''
        if self._colorMidiLeftNote is not None:
            return self._colorMidiLeftNote
        if self.score is None:
            print('Warning: Note has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalNote.colorLeftMidiNote
    
    @colorMidiLeftNote.setter
    def colorMidiLeftNote(self, value: Optional[str]):
        '''Set left MIDI note color - use None to reset to inheritance.'''
        self._colorMidiLeftNote = value
    
    # Property: colorMidiRightNote
    @property
    def colorMidiRightNote(self) -> str:
        '''Get right MIDI note color - inherits from globalNote.colorRightMidiNote if None.'''
        if self._colorMidiRightNote is not None:
            return self._colorMidiRightNote
        if self.score is None:
            print('Warning: Note has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalNote.colorRightMidiNote
    
    @colorMidiRightNote.setter
    def colorMidiRightNote(self, value: Optional[str]):
        '''Set right MIDI note color - use None to reset to inheritance.'''
        self._colorMidiRightNote = value
    
    # Property: colorMidiNote (hand-dependent inheritance - deprecated, use colorMidiLeftNote/colorMidiRightNote)
    @property
    def colorMidiNote(self) -> str:
        '''Get MIDI note color - inherits based on hand (left '<' or right '>').'''
        if self.hand == '<':
            return self.colorMidiLeftNote
        else:
            return self.colorMidiRightNote
    
    @colorMidiNote.setter
    def colorMidiNote(self, value: Optional[str]):
        '''Set MIDI note color for current hand.'''
        if self.hand == '<':
            self._colorMidiLeftNote = value
        else:
            self._colorMidiRightNote = value
    
    # Property: blackNoteDirection
    @property
    def blackNoteDirection(self) -> Literal['^', 'v']:
        '''Get black note direction - inherits from globalNote.blackNoteDirection if None.'''
        if self._blackNoteDirection is not None:
            return self._blackNoteDirection
        if self.score is None:
            return 'v'  # Fallback if no score reference
        return self.score.properties.globalNote.blackNoteDirection
    
    @blackNoteDirection.setter
    def blackNoteDirection(self, value: Optional[Literal['^', 'v']]):
        '''Set black note direction - use None to reset to inheritance.'''
        self._blackNoteDirection = value
    
    # Property: stemLength
    @property
    def stemLengthMm(self) -> float:
        '''Get stem length - inherits from globalNote.stemLength if None.'''
        if self._stemLengthMm is not None:
            return self._stemLengthMm
        if self.score is None:
            return 10.0  # Fallback if no score reference
        return self.score.properties.globalNote.stemLengthMm
    
    @stemLengthMm.setter
    def stemLengthMm(self, value: Optional[float]):
        '''Set stem length - use None to reset to inheritance.'''
        self._stemLengthMm = value
