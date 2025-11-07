from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import List, Literal

@dataclass_json
@dataclass
class GlobalNote:
    color: str = '#000000'
    colorLeftMidiNote: str = '#000000'
    colorRightMidiNote: str = '#000000'
    stemWidth: float = 1.0
    stemLength: float = 10.0
    beamWidth: float = 1.0
    blackNoteDirection: Literal['^', 'v'] = 'v'
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
    width: float = 4.0
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
    width: float = 1.0
    dashPattern: List[int] = field(default_factory=list)
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalSlur:
    color: str = '#000000'
    middleWidth: float = 1.0
    startEndWidth: float = .5
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
    width: float = 1.0
    visible: int = field(default=1, metadata=config(field_name='visible?'))

@dataclass_json
@dataclass
class GlobalBasegrid:
    gridlineColor: str = '#000000'
    gridlineWidth: float = .125
    gridlineDashPattern: List[float] = field(default_factory=lambda: [2, 2])
    gridlineVisible: int = field(default=1, metadata=config(field_name='gridlineVisible?'))
    barlineColor: str = '#000000'
    barlineWidth: float = .25
    barlineVisible: int = field(default=1, metadata=config(field_name='barlineVisible?'))

@dataclass_json
@dataclass
class GlobalMeasureNumbering:
    color: str = '#000000'
    fontSize: int = 12
    visible: int = field(default=1, metadata=config(field_name='measureNumberingVisible?'))
    inStepsOf: int = field(default=1, metadata=config(field_name='inStepsOf'))
    skipCount: list[int] = field(default_factory=list)


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