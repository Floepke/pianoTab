from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

@dataclass
@dataclass_json
class FileSettings:
    '''
    Settings that have heavy specific impact on the specific file being edited.
    '''
    
    quarterNoteUnit: float = field(
        default=256.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Quarter note time unit: fundamental temporal resolution (how many units = one quarter note). Default 256.0 means whole note = 1024, eighth = 128. All event times/durations reference this base unit. WARNING: Changing this after score creation rescales the entire timeline and changes meaning of all existing time values. In normal usage don\'t touch it :)',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 1.0,
                'step': 1.0,
            }
        }
    )
    zoomPixelsQuarter: float = field(
        default=100.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Zoom level in pixels per quarter note. Adjusts the horizontal zoom of the timeline in the editor. Default is 1.0 (256 pixels per quarter note). Higher values zoom in, lower values zoom out.',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.1,
                'step': 0.1,
            }
        }
    )
    _editorRenderedStave: int = field(
        default=1,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Currently selected stave index in the editor (1-based so 1 is the first stave). Sets which stave is currently rendered in the editor view.',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'step': 1,
            }
        }
    )
    drawScale: float = field(
        default=0.75,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global drawing scale multiplier (affects all rendered elements)',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.1,
                'max': 5.0,
                'step': 0.05,
            }
        }
    )
    
    @property
    def editorRenderedStave(self) -> int:
        '''Get the current rendered stave index (1-based for user interface).'''
        return self._editorRenderedStave
    
    @editorRenderedStave.setter
    def editorRenderedStave(self, value: int):
        '''Set the current rendered stave index (1-based for user interface).'''
        self._editorRenderedStave = max(1, int(value))
    
    def get_rendered_stave_index(self, num_staves: int = None) -> int:
        '''Get the 0-based stave index for internal use.
        
        Args:
            num_staves: Total number of staves in the score. If provided, uses modulo
                       to ensure the index wraps around and never exceeds bounds.
        
        Returns:
            0-based stave index, wrapped if num_staves is provided.
        '''
        index = max(0, self._editorRenderedStave - 1)
        if num_staves is not None and num_staves > 0:
            index = index % num_staves
        return index
    
    def set_rendered_stave_index(self, index: int):
        '''Set the 0-based stave index for internal use.'''
        self._editorRenderedStave = max(1, index + 1)