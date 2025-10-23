from pydantic import BaseModel, Field
from typing import List, Literal
from file.globalProperties import (
        GlobalNote, GlobalArticulation, GlobalBeam, 
        GlobalGracenote, GlobalCountline, GlobalSlur, 
        GlobalText, GlobalBarline, GlobalBasegrid, 
        GlobalStave, GlobalPage, GlobalSection,
        GlobalStartRepeat, GlobalEndRepeat
    )

class Properties(BaseModel):
    globalNote: GlobalNote = Field(default_factory=GlobalNote)
    globalArticulation: GlobalArticulation = Field(default_factory=GlobalArticulation)
    globalBeam: GlobalBeam = Field(default_factory=GlobalBeam)
    globalGraceNote: GlobalGracenote = Field(default_factory=GlobalGracenote)
    globalCountLine: GlobalCountline = Field(default_factory=GlobalCountline)
    globalSlur: GlobalSlur = Field(default_factory=GlobalSlur)
    globalText: GlobalText = Field(default_factory=GlobalText)
    globalBarLine: GlobalBarline = Field(default_factory=GlobalBarline)
    globalBasegrid: GlobalBasegrid = Field(default_factory=GlobalBasegrid)
    globalStave: GlobalStave = Field(default_factory=GlobalStave)
    globalPage: GlobalPage = Field(default_factory=GlobalPage)
    globalSection: GlobalSection = Field(default_factory=GlobalSection)
    globalStartRepeat: GlobalStartRepeat = Field(default_factory=GlobalStartRepeat)
    globalEndrepeat: GlobalEndRepeat = Field(default_factory=GlobalEndRepeat)
    editorZoomPixelsQuarter: int = Field(default=100)
    stopSignType: Literal['PianoTab', 'Klavarskribo'] = Field(default='PianoTab')
    drawScale: float = Field(default=0.75)