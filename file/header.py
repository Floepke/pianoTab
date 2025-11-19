from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import time

@dataclass_json
@dataclass
class Header:
    title: str = field(
        default='myTitle',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Score title',
            'tree_edit_type': 'text',
        }
    )
    subtitle: str = field(
        default='mySubtitle',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Score subtitle',
            'tree_edit_type': 'text',
        }
    )
    composer: str = field(
        default='myComposer',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Composer name',
            'tree_edit_type': 'text',
        }
    )
    arranger: str = field(
        default='',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Arranger name',
            'tree_edit_type': 'text',
        }
    )
    lyricist: str = field(
        default='',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Lyricist name',
            'tree_edit_type': 'text',
        }
    )
    publisher: str = field(
        default='',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Publisher name',
            'tree_edit_type': 'text',
        }
    )
    copyright: str = field(
        default_factory=lambda: f'Copyright © {time.strftime('%Y')}, pianoTAB. All rights reserved.',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Copyright notice',
            'tree_edit_type': 'text',
        }
    )
    created: str = field(
        default_factory=lambda: time.strftime('%d-%m-%Y_%H:%M:%S'),
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'File creation timestamp',
            'tree_edit_type': 'readonly',
        }
    )
    modificationStamp: str = field(
        default_factory=lambda: time.strftime('%d-%m-%Y_%H:%M:%S'),
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Modification timestamp, this value get\'s updated every time we save the file.',
            'tree_edit_type': 'readonly',
        }
    )
    genre: str = field(
        default='',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Musical genre',
            'tree_edit_type': 'text',
        }
    )
    comment: str = field(
        default='',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Additional comments or notes',
            'tree_edit_type': 'text',
        }
    )
