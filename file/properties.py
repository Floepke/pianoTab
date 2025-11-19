from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Literal
from file.globalProperties import (
        GlobalNote, GlobalArticulation, GlobalBeam, 
        GlobalGraceNote, GlobalCountLine, GlobalSlur, 
        GlobalText, GlobalBasegrid, 
        GlobalStave, GlobalPage, GlobalSection,
        GlobalStartRepeat, GlobalEndRepeat, GlobalMeasureNumbering
    )

@dataclass_json
@dataclass
class Properties:
    globalNote: GlobalNote = field(
        default_factory=GlobalNote,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all notes',
            'tree_edit_type': 'readonly',
        }
    )
    globalArticulation: GlobalArticulation = field(
        default_factory=GlobalArticulation,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all articulations',
            'tree_edit_type': 'readonly',
        }
    )
    globalBeam: GlobalBeam = field(
        default_factory=GlobalBeam,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all beams',
            'tree_edit_type': 'readonly',
        }
    )
    globalGraceNote: GlobalGraceNote = field(
        default_factory=GlobalGraceNote,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all grace notes',
            'tree_edit_type': 'readonly',
        }
    )
    globalCountLine: GlobalCountLine = field(
        default_factory=GlobalCountLine,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all count lines',
            'tree_edit_type': 'readonly',
        }
    )
    globalSlur: GlobalSlur = field(
        default_factory=GlobalSlur,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all slurs',
            'tree_edit_type': 'readonly',
        }
    )
    globalText: GlobalText = field(
        default_factory=GlobalText,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for all text annotations',
            'tree_edit_type': 'readonly',
        }
    )
    globalBasegrid: GlobalBasegrid = field(
        default_factory=GlobalBasegrid,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for grid and bar lines',
            'tree_edit_type': 'readonly',
        }
    )
    globalMeasureNumbering: GlobalMeasureNumbering = field(
        default_factory=GlobalMeasureNumbering,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for measure numbering',
            'tree_edit_type': 'readonly',
        }
    )
    globalStave: GlobalStave = field(
        default_factory=GlobalStave,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for stave markers',
            'tree_edit_type': 'readonly',
        }
    )
    globalPage: GlobalPage = field(
        default_factory=GlobalPage,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global page layout and margin settings',
            'tree_edit_type': 'readonly',
        }
    )
    globalSection: GlobalSection = field(
        default_factory=GlobalSection,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for section markers',
            'tree_edit_type': 'readonly',
        }
    )
    globalStartRepeat: GlobalStartRepeat = field(
        default_factory=GlobalStartRepeat,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for start repeat markers',
            'tree_edit_type': 'readonly',
        }
    )
    globalEndrepeat: GlobalEndRepeat = field(
        default_factory=GlobalEndRepeat,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Global default properties for end repeat markers',
            'tree_edit_type': 'readonly',
        }
    )
    editorZoomPixelsQuarter: int = field(
        default=250,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Editor zoom: pixels per quarter note (for vertical time axis)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 10,
                'max': 1000,
                'step': 10,
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