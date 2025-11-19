from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class GraceNote:
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique grace note identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Time position for grace note',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    pitch: int = field(
        default=60,
        metadata={
            'tree_icon': 'note',
            'tree_tooltip': 'Grace note pitch (key 1-88, C4=40)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 88,
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
    
    # Storage field for inherited property (serializes to JSON with clean name)
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Grace note color (None = inherit from globalGraceNote)',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    
    def __post_init__(self):
        '''Initialize score reference as a non-dataclass attribute.'''
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        '''Get color - inherits from globalGraceNote.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: GraceNote has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalGraceNote.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value