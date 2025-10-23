from pydantic import BaseModel, Field
from typing import List, Literal

class GlobalNote(BaseModel):
    color: str = Field(default='#000000')
    colorLeftMidiNote: str = Field(default='#000000')
    colorRightMidiNote: str = Field(default='#000000')
    stemWidth: float = Field(default=1.0)
    stemLength: float = Field(default=10.0)
    beamWidth: float = Field(default=1.0)
    blackNoteDirection: Literal['^', 'v'] = Field(default='v')
    noteHeadVisible: bool = Field(default=True)
    stemVisible: bool = Field(default=True)
    midiNoteVisible: bool = Field(default=True)
    accidentalVisible: bool = Field(default=True)
    noteStopVisible: bool = Field(default=True)
    continuationDotVisible: bool = Field(default=True)
    leftDotVisible: bool = Field(default=True)

class GlobalArticulation(BaseModel):
    color: str = Field(default='#000000')
    visible: bool = Field(default=True)

class GlobalBeam(BaseModel):
    color: str = Field(default='#000000')
    width: float = Field(default=4.0)
    slant: float = Field(default=5.0)
    visible: int = Field(default=True)

class GlobalGracenote(BaseModel):
    color: str = Field(default='#000000')
    visible: int = Field(default=True)

class GlobalCountline(BaseModel):
    color: str = Field(default='#000000')
    width: float = Field(default=1.0)
    sideWidth: float = Field(default=0.5)
    dashPattern: List[int] = Field(default_factory=list)
    visible: int = Field(default=True)

class GlobalSlur(BaseModel):
    color: str = Field(default='#000000')
    middleWidth: float = Field(default=1.0)
    startEndWidth: float = Field(default=.5)
    visible: int = Field(default=True)

class GlobalText(BaseModel):
    fontSize: int = Field(default=12)
    family: str = Field(default='Courier New')
    color: str = Field(default='#000000')

class GlobalBarline(BaseModel):
    color: str = Field(default='#000000')
    width: float = Field(default=1.0)
    visible: int = Field(default=True)

class GlobalBasegrid(BaseModel):
    gridlineColor: str = Field(default='#000000')
    gridlineWidth: float = Field(default=1.0)
    gridLineDashPattern: List[int] = Field(default_factory=lambda: [4, 4])
    barlineColor: str = Field(default='#000000')
    barlineWidth: float = Field(default=2.0)
    fontSize: int = Field(default=12)

class GlobalStave(BaseModel):
    twoLineColor: str = Field(default='#000000')
    threeLineColor: str = Field(default='#000000')
    clefColor: str = Field(default='#000000')
    twoLineWidth: float = Field(default=1.0)
    threeLineWidth: float = Field(default=2.0)
    clefWidth: float = Field(default=1.0)
    visible: int = Field(default=True)
    clefDashPattern: List[int] = Field(default_factory=lambda: [4, 4])

class GlobalPage(BaseModel):
    # all measurements in mm:
    width: float = Field(default=210.0)
    height: float = Field(default=297.0)
    marginLeft: float = Field(default=5.0)
    marginRight: float = Field(default=5.0)
    marginUp: float = Field(default=10.0)
    marginDown: float = Field(default=10.0)
    headerHeight: float = Field(default=12.5)
    footerHeight: float = Field(default=12.5)

class GlobalSection(BaseModel):
    color: str = Field(default='#000000')
    lineWidth: float = Field(default=1.0)
    visible: bool = Field(default=True)

class GlobalStartRepeat(BaseModel):
    color: str = Field(default='#000000')
    lineWidth: float = Field(default=1.0)
    visible: bool = Field(default=True)

class GlobalEndRepeat(BaseModel):
    color: str = Field(default='#000000')
    lineWidth: float = Field(default=1.0)
    visible: bool = Field(default=True)