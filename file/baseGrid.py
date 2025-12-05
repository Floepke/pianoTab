from typing import List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

@dataclass_json
@dataclass
class BaseGrid:
    numerator: int = field(
        default=4,
        metadata={
            **config(field_name='numerator'),
            'tree_icon': 'property',
            'tree_tooltip': 'Time signature numerator (beats per measure)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 32,
                'step': 1,
            }
        }
    )
    denominator: int = field(
        default=4,
        metadata={
            **config(field_name='denominator'),
            'tree_icon': 'property',
            'tree_tooltip': 'Time signature denominator (note value per beat)',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': [1, 2, 4, 8, 16, 32, 64, 128],
                'choice_labels': ['1', '2', '4', '8', '16', '32', '64', '128'],
            }
        }
    )
    gridTimes: List[float] = field(
        default_factory=lambda: [100.0, 512.0, 768.0],
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Grid line time positions within measure',
            'tree_edit_type': 'list',
        }
    )
    measureAmount: int = field(
        default=8,
        metadata={
            **config(field_name='measureAmount'),
            'tree_icon': 'property',
            'tree_tooltip': 'Number of measures in this grid section',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 1000,
                'step': 1,
            }
        }
    )
    timeSignatureIndicatorVisible: int = field(
        default=1,
        metadata={
            **config(field_name='timeSignatureIndicatorVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show time signature indicator',
            'tree_edit_type': 'bool',
        }
    )
