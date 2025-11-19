from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import Literal, TYPE_CHECKING, Optional
if TYPE_CHECKING: 
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Text:
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique text annotation identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Vertical time position for text annotation',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    side: Literal['<', '>'] = field(
        default='>',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Side of staff: < = left, > = right',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['<', '>'],
                'choice_labels': ['Left', 'Right'],
            }
        }
    )
    distFromSide: float = field(
        default=10.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Distance from staff side in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 1.0,
            }
        }
    )
    text: str = field(
        default='Text',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Text content to display',
            'tree_edit_type': 'text',
        }
    )
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _fontSize: Optional[int] = field(
        default=None,
        metadata={
            **config(field_name='fontSize'),
            'tree_icon': 'property',
            'tree_tooltip': 'Font size in points (None = inherit from globalText)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 144,
                'step': 1,
                'allow_none': True,
            }
        }
    )
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Text color (None = inherit from globalText)',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    
    def __post_init__(self):
        '''Initialize score reference as a non-dataclass attribute.'''
        self.score: Optional['SCORE'] = None
    
    # Property: fontSize
    @property
    def fontSize(self) -> int:
        '''Get fontSize - inherits from globalText.fontSize if None.'''
        if self._fontSize is not None:
            return self._fontSize
        if self.score is None:
            print('Warning: Text has no score reference for property inheritance.')
            return 12  # Fallback if no score reference
        return self.score.properties.globalText.fontSize
    
    @fontSize.setter
    def fontSize(self, value: Optional[int]):
        '''Set fontSize - use None to reset to inheritance.'''
        self._fontSize = value
    
    # Property: color
    @property
    def color(self) -> str:
        '''Get color - inherits from globalText.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: Text has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalText.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
