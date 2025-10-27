from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Literal
from file.globalProperties import (
        GlobalNote, GlobalArticulation, GlobalBeam, 
        GlobalGracenote, GlobalCountline, GlobalSlur, 
        GlobalText, GlobalBarline, GlobalBasegrid, 
        GlobalStave, GlobalPage, GlobalSection,
        GlobalStartRepeat, GlobalEndRepeat
    )

@dataclass_json
@dataclass
class Properties:
    globalNote: GlobalNote = field(default_factory=GlobalNote)
    globalArticulation: GlobalArticulation = field(default_factory=GlobalArticulation)
    globalBeam: GlobalBeam = field(default_factory=GlobalBeam)
    globalGraceNote: GlobalGracenote = field(default_factory=GlobalGracenote)
    globalCountLine: GlobalCountline = field(default_factory=GlobalCountline)
    globalSlur: GlobalSlur = field(default_factory=GlobalSlur)
    globalText: GlobalText = field(default_factory=GlobalText)
    globalBarLine: GlobalBarline = field(default_factory=GlobalBarline)
    globalBasegrid: GlobalBasegrid = field(default_factory=GlobalBasegrid)
    globalStave: GlobalStave = field(default_factory=GlobalStave)
    globalPage: GlobalPage = field(default_factory=GlobalPage)
    globalSection: GlobalSection = field(default_factory=GlobalSection)
    globalStartRepeat: GlobalStartRepeat = field(default_factory=GlobalStartRepeat)
    globalEndrepeat: GlobalEndRepeat = field(default_factory=GlobalEndRepeat)
    editorZoomPixelsQuarter: int = 100
    stopSignType: Literal['PianoTab', 'Klavarskribo'] = 'PianoTab'
    drawScale: float = 0.75