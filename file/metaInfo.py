from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import time

@dataclass_json
@dataclass
class MetaInfo:
    appName: str = field(
        default='pianoTAB',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Application name',
            'tree_edit_type': 'readonly',
        }
    )
    extension: str = field(
        default='.piano',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'File extension',
            'tree_edit_type': 'readonly',
        }
    )
    description: str = field(
        default='pianoTAB score file',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'File format description',
            'tree_edit_type': 'readonly',
        }
    )
    version: str = field(
        default='1.0',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'File format version',
            'tree_edit_type': 'readonly',
        }
    )
    author: str = field(
        default='pianoTAB Team',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'File format author',
            'tree_edit_type': 'readonly',
        }
    )
    license: str = field(
        default='MIT',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'File format license',
            'tree_edit_type': 'readonly',
        }
    )