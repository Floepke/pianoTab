from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import TYPE_CHECKING, Union, Literal, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Articulation:
    # Core fields
    type: str = field(
        default='staccato',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Articulation type (e.g., staccato, accent, tenuto)',
            'tree_edit_type': 'text',
        }
    )
    xOffset: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Horizontal offset from default position',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'step': 0.5,
            }
        }
    )
    yOffset: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Vertical offset from default position',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'step': 0.5,
            }
        }
    )

    # Storage field for inherited property (serializes to JSON with clean name)
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Articulation color (None = inherit from globalArticulation)',
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
        '''Get color - inherits from globalArticulation.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: Articulation has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalArticulation.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
