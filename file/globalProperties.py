from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import List, Literal

@dataclass_json
@dataclass
class GlobalNote:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for note heads',
            'tree_edit_type': 'color',
        }
    )
    colorLeftMidiNote: str = field(
        default='#FFD24D',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default MIDI rectangle color for left hand notes',
            'tree_edit_type': 'color',
        }
    )
    colorRightMidiNote: str = field(
        default='#FFD24D',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default MIDI rectangle color for right hand notes',
            'tree_edit_type': 'color',
        }
    )
    stemWidthMm: float = field(
        default=.25,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default stem width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.05,
            }
        }
    )
    stemLengthMm: float = field(
        default=10.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default stem length in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 50.0,
                'step': 0.5,
            }
        }
    )
    beamWidthMm: float = field(
        default=.25,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default beam width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.05,
            }
        }
    )
    blackNoteDirection: Literal['^', 'v'] = field(
        default='v',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default stem direction for black notes',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['^', 'v'],
                'choice_labels': ['Up', 'Down'],
                'choice_icons': ['blacknoteup', 'blacknotedown'],
            }
        }
    )
    leftDotSizeScale: float = field(
        default=.3,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Continuation dot size relative to note head (0.0-1.0)',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 1.0,
                'step': 0.05,
            }
        }
    )
    noteHeadVisible: int = field(
        default=1,
        metadata={
            **config(field_name='noteHeadVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show note heads by default',
            'tree_edit_type': 'bool',
        }
    )
    stemVisible: int = field(
        default=1,
        metadata={
            **config(field_name='stemVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show note stems by default',
            'tree_edit_type': 'bool',
        }
    )
    midiNoteVisible: int = field(
        default=1,
        metadata={
            **config(field_name='midiNoteVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show MIDI rectangles by default',
            'tree_edit_type': 'bool',
        }
    )
    accidentalVisible: int = field(
        default=1,
        metadata={
            **config(field_name='accidentalVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show accidental marks by default',
            'tree_edit_type': 'bool',
        }
    )
    noteStopVisible: int = field(
        default=1,
        metadata={
            **config(field_name='noteStopVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show note stop markers by default',
            'tree_edit_type': 'bool',
        }
    )
    continuationDotVisible: int = field(
        default=1,
        metadata={
            **config(field_name='continuationDotVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show continuation dots by default',
            'tree_edit_type': 'bool',
        }
    )
    leftDotVisible: int = field(
        default=1,
        metadata={
            **config(field_name='leftDotVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show left dots by default',
            'tree_edit_type': 'bool',
        }
    )
    stopSignType: Literal['pianoTAB', 'Klavarskribo'] = field(
        default='pianoTAB',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Note stop sign notation style',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['pianoTAB', 'Klavarskribo'],
                'choice_labels': ['pianoTAB', 'Klavarskribo'],
            }
        }
    )
    stopSignColor: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for note stop signs',
            'tree_edit_type': 'color',
        }
    )

@dataclass_json
@dataclass
class GlobalArticulation:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for articulation marks',
            'tree_edit_type': 'color',
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show articulation marks by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalBeam:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for beams',
            'tree_edit_type': 'color',
        }
    )
    widthMm: float = field(
        default=4.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default beam width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 20.0,
                'step': 0.5,
            }
        }
    )
    slant: float = field(
        default=5.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default beam slant angle in degrees',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 45.0,
                'step': 1.0,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show beams by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalGraceNote:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for grace notes',
            'tree_edit_type': 'color',
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show grace notes by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalCountLine:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for count lines',
            'tree_edit_type': 'color',
        }
    )
    widthMm: float = field(
        default=1.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default count line width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
            }
        }
    )
    dashPattern: List[int] = field(
        default_factory=list,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default dash pattern for count lines (empty = solid)',
            'tree_edit_type': 'list',
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show count lines by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalSlur:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for slurs',
            'tree_edit_type': 'color',
        }
    )
    middleWidthMm: float = field(
        default=1.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default slur middle width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
            }
        }
    )
    startEndWidthMm: float = field(
        default=.5,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default slur start/end width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show slurs by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalText:
    size: int = field(
        default=12,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default text font size in points',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 144,
                'step': 1,
            }
        }
    )
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default text color',
            'tree_edit_type': 'color',
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show text annotations by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalBasegrid:
    gridlineColor: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for grid lines',
            'tree_edit_type': 'color',
        }
    )
    gridlineWidthMm: float = field(
        default=.125,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default grid line width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.025,
            }
        }
    )
    gridlineDashPattern: List[float] = field(
        default_factory=lambda: [2, 2],
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default dash pattern for grid lines',
            'tree_edit_type': 'list',
        }
    )
    gridlineVisible: int = field(
        default=1,
        metadata={
            **config(field_name='gridlineVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show grid lines by default',
            'tree_edit_type': 'bool',
        }
    )
    barlineColor: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for bar lines',
            'tree_edit_type': 'color',
        }
    )
    barlineWidthMm: float = field(
        default=.25,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default bar line width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.025,
            }
        }
    )
    barlineVisible: int = field(
        default=1,
        metadata={
            **config(field_name='barlineVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show bar lines by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalMeasureNumbering:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for measure numbers',
            'tree_edit_type': 'color',
        }
    )
    fontSize: int = field(
        default=12,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default font size for measure numbers',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 72,
                'step': 1,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='measureNumberingVisible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show measure numbers by default',
            'tree_edit_type': 'bool',
        }
    )
    inStepsOf: int = field(
        default=1,
        metadata={
            **config(field_name='inStepsOf'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show measure numbers every N measures (ignored if numberAtStartOfLine is enabled)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 100,
                'step': 1,
            }
        }
    )
    skipCount: list[int] = field(
        default_factory=list,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'List of measure numbers to skip (e.g., [1, 5, 10])',
            'tree_edit_type': 'list',
        }
    )
    numberFromStartOfLine: int = field(
        default=0,
        metadata={
            **config(field_name='numberAtStartOfLine?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Only show measure numbers at the start of each line',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalStave:
    twoLineColor: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for two-line stave marks',
            'tree_edit_type': 'color',
        }
    )
    threeLineColor: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for three-line stave marks',
            'tree_edit_type': 'color',
        }
    )
    clefColor: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for clef markers',
            'tree_edit_type': 'color',
        }
    )
    twoLineWidth: float = field(
        default=.125,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default width for two-line stave marks in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.025,
            }
        }
    )
    threeLineWidth: float = field(
        default=.25,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default width for three-line stave marks in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.025,
            }
        }
    )
    clefWidth: float = field(
        default=.125,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default width for clef markers in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 5.0,
                'step': 0.025,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show stave marks by default',
            'tree_edit_type': 'bool',
        }
    )
    clefDashPattern: List[float] = field(
        default_factory=lambda: [2, 2],
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default dash pattern for clef markers',
            'tree_edit_type': 'list',
        }
    )

@dataclass_json
@dataclass
class GlobalPage:
    # all measurements in mm:
    width: float = field(
        default=210.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Page width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 50.0,
                'max': 1000.0,
                'step': 1.0,
            }
        }
    )
    height: float = field(
        default=297.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Page height in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 50.0,
                'max': 1000.0,
                'step': 1.0,
            }
        }
    )
    marginLeft: float = field(
        default=5.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Left page margin in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 0.5,
            }
        }
    )
    marginRight: float = field(
        default=5.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Right page margin in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 0.5,
            }
        }
    )
    marginUp: float = field(
        default=10.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Top page margin in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 0.5,
            }
        }
    )
    marginDown: float = field(
        default=10.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Bottom page margin in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 0.5,
            }
        }
    )
    headerHeight: float = field(
        default=12.5,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Page header height in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 0.5,
            }
        }
    )
    footerHeight: float = field(
        default=12.5,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Page footer height in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 100.0,
                'step': 0.5,
            }
        }
    )

@dataclass_json
@dataclass
class GlobalSection:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for section markers',
            'tree_edit_type': 'color',
        }
    )
    lineWidth: float = field(
        default=1.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default section marker line width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show section markers by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalStartRepeat:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for start repeat markers',
            'tree_edit_type': 'color',
        }
    )
    lineWidth: float = field(
        default=1.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default start repeat line width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show start repeat markers by default',
            'tree_edit_type': 'bool',
        }
    )

@dataclass_json
@dataclass
class GlobalEndRepeat:
    color: str = field(
        default='#000000',
        metadata={
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Default color for end repeat markers',
            'tree_edit_type': 'color',
        }
    )
    lineWidth: float = field(
        default=1.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Default end repeat line width in millimeters',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
            }
        }
    )
    visible: int = field(
        default=1,
        metadata={
            **config(field_name='visible?'),
            'tree_icon': 'property',
            'tree_tooltip': 'Show end repeat markers by default',
            'tree_edit_type': 'bool',
        }
    )