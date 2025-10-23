from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class GlobalNote:
    color: str = '#000000'
    colorLeftMidiNote: str = '#000000'
    colorRightMidiNote: str = '#000000'
    stemWidth: float = 1.0
    stemLength: float = 10.0
    beamWidth: float = 1.0
    blackNoteDirection: Literal['^', 'v'] = 'v'
    noteHeadVisible: bool = True
    stemVisible: bool = True
    midiNoteVisible: bool = True
    accidentalVisible: bool = True
    noteStopVisible: bool = True
    continuationDotVisible: bool = True
    leftDotVisible: bool = True

@dataclass
class GlobalArticulation:
    color: str = '#000000'
    visible: bool = True

@dataclass
class GlobalBeam:
    color: str = '#000000'
    width: float = 4.0
    slant: float = 5.0
    visible: int = True

@dataclass
class GlobalGracenote:
    color: str = '#000000'
    visible: int = True

@dataclass
class GlobalCountline:
    color: str = '#000000'
    width: float = 1.0
    dashPattern: List[int] = field(default_factory=list)
    visible: int = True

@dataclass
class GlobalSlur:
    color: str = '#000000'
    middleWidth: float = 1.0
    startEndWidth: float = .5
    visible: int = True

@dataclass
class GlobalText:
    fontSize: int = 12
    family: str = 'Courier New'
    color: str = '#000000'

@dataclass
class GlobalBarline:
    color: str = '#000000'
    width: float = 1.0
    visible: int = True

@dataclass
class GlobalBasegrid:
    gridlineColor: str = '#000000'
    gridlineWidth: float = 1.0
    gridLineDashPattern: List[int] = field(default_factory=lambda: [4, 4])
    barlineColor: str = '#000000'
    barlineWidth: float = 2.0
    fontSize: int = 12

@dataclass
class GlobalStave:
    twoLineColor: str = '#000000'
    threeLineColor: str = '#000000'
    clefColor: str = '#000000'
    twoLineWidth: float = 1.0
    threeLineWidth: float = 2.0
    clefWidth: float = 1.0
    visible: int = True
    clefDashPattern: List[int] = field(default_factory=lambda: [4, 4])

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

@dataclass
class GlobalSection:
    color: str = '#000000'
    lineWidth: float = 1.0
    visible: bool = True

@dataclass
class GlobalStartRepeat:
    color: str = '#000000'
    lineWidth: float = 1.0
    visible: bool = True

@dataclass
class GlobalEndRepeat:
    color: str = '#000000'
    lineWidth: float = 1.0
    visible: bool = True