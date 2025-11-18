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
    globalNote: GlobalNote = field(default_factory=GlobalNote)
    globalArticulation: GlobalArticulation = field(default_factory=GlobalArticulation)
    globalBeam: GlobalBeam = field(default_factory=GlobalBeam)
    globalGraceNote: GlobalGraceNote = field(default_factory=GlobalGraceNote)
    globalCountLine: GlobalCountLine = field(default_factory=GlobalCountLine)
    globalSlur: GlobalSlur = field(default_factory=GlobalSlur)
    globalText: GlobalText = field(default_factory=GlobalText)
    globalBasegrid: GlobalBasegrid = field(default_factory=GlobalBasegrid)
    globalMeasureNumbering: GlobalMeasureNumbering = field(default_factory=GlobalMeasureNumbering)
    globalStave: GlobalStave = field(default_factory=GlobalStave)
    globalPage: GlobalPage = field(default_factory=GlobalPage)
    globalSection: GlobalSection = field(default_factory=GlobalSection)
    globalStartRepeat: GlobalStartRepeat = field(default_factory=GlobalStartRepeat)
    globalEndrepeat: GlobalEndRepeat = field(default_factory=GlobalEndRepeat)
    editorZoomPixelsQuarter: int = 250
    drawScale: float = 0.75