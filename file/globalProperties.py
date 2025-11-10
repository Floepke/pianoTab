from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import List, Literal

@dataclass_json
@dataclass
class GlobalNote:
    color: str = '#000000'
    colorLeftMidiNote: str = '#dddddd'
    colorRightMidiNote: str = '#dddddd'
    stemWidthMm: float = .25
    stemLengthMm: float = 10.0
    beamWidthMm: float = .25
    blackNoteDirection: Literal['^', 'v'] = 'v'
    leftDotSizeScale: float = .3 # value between 0.0 and 1.0, the dot get's the size relative to the notehead size
    noteHeadVisible: int = field(default=1, metadata=config(field_name='noteHeadVisible?'))
    stemVisible: int = field(default=1, metadata=config(field_name='stemVisible?'))
    midiNoteVisible: int = field(default=1, metadata=config(field_name='midiNoteVisible?'))
    accidentalVisible: int = field(default=1, metadata=config(field_name='accidentalVisible?'))
    noteStopVisible: int = field(default=1, metadata=config(field_name='noteStopVisible?'))
    continuationDotVisible: int = field(default=1, metadata=config(field_name='continuationDotVisible?'))
    leftDotVisible: int = field(default=1, metadata=config(field_name='leftDotVisible?'))

@dataclass_json
@dataclass
class GlobalArticulation:
    color: str = '#000000'
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalBeam:
    color: str = '#000000'
    widthMm: float = 4.0
    slant: float = 5.0
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalGraceNote:
    color: str = '#000000'
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalCountLine:
    color: str = '#000000'
    widthMm: float = 1.0
    dashPattern: List[int] = field(default_factory=list)
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalSlur:
    color: str = '#000000'
    middleWidthMm: float = 1.0
    startEndWidthMm: float = .5
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalText:
    size: int = 12
    color: str = '#000000'
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalBarline:
    color: str = '#000000'
    widthMm: float = 1.0
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalBasegrid:
    gridlineColor: str = '#000000'
    gridlineWidthMm: float = .125
    gridlineDashPattern: List[float] = field(default_factory=lambda: [2, 2])
    gridlineVisible: int = field(default=1, metadata=config(field_name='gridlineVisible?'))
    barlineColor: str = '#000000'
    barlineWidthMm: float = .25
    barlineVisible: int = field(default=1, metadata=config(field_name='barlineVisible?'))

@dataclass_json
@dataclass
class GlobalMeasureNumbering:
    color: str = '#000000'
    fontSize: int = 12
    visible: int = field(default=1, metadata=config(field_name='measureNumberingVisible?'))
    inStepsOf: int = field(default=1, metadata=config(field_name='inStepsOf')) # show measure numbers in steps of N measures, ignored if numberAtStartOfLine == True
    skipCount: list[int] = field(default_factory=list) # list of measures that are skipped (e.g. [1, 5, 10] to skip measures 1, 5 and 10)
    numberFromStartOfLine: int = field(default=0, metadata=config(field_name='numberAtStartOfLine?')) # if true, measure numbers are only shown at the start of a new line

@dataclass_json
@dataclass
class GlobalStave:
    twoLineColor: str = '#000000'
    threeLineColor: str = '#000000'
    clefColor: str = '#000000'
    twoLineWidth: float = .125
    threeLineWidth: float = .25
    clefWidth: float = .125
    visible: int = field(default=1, metadata=config(field_name='visible?'))
    clefDashPattern: List[float] = field(default_factory=lambda: [2, 2])

@dataclass_json
@dataclass
class GlobalPage:
    # all measurements in mm:
    width: float = 210.0
    height: float = 297.0
    marginLeft: float = 5.0
    marginRight: float = 5.0
    marginUp: float = 10.0
    marginDown: float = 10.0
    headerHeight: float = 12.5
    footerHeight: float = 12.5

@dataclass_json
@dataclass
class GlobalSection:
    color: str = '#000000'
    lineWidth: float = 1.0
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalStartRepeat:
    color: str = '#000000'
    lineWidth: float = 1.0
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalEndRepeat:
    color: str = '#000000'
    lineWidth: float = 1.0
    visible: int = field(default=1, metadata=config(field_name='visible?'))