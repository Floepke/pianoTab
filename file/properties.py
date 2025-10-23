from dataclasses import dataclass, field
from typing import List, Literal
from file.globalProperties import (
        GlobalNote, GlobalArticulation, GlobalBeam, 
        GlobalGracenote, GlobalCountline, GlobalSlur, 
        GlobalText, GlobalBarline, GlobalBasegrid, 
        GlobalStave, GlobalPage, GlobalSection,
        GlobalStartRepeat, GlobalEndRepeat
    )

@dataclass
class Properties:
    globalNote: GlobalNote = field(default_factory=lambda: GlobalNote())
    globalArticulation: GlobalArticulation = field(default_factory=lambda: GlobalArticulation())
    globalBeam: GlobalBeam = field(default_factory=lambda: GlobalBeam())
    globalGraceNote: GlobalGracenote = field(default_factory=lambda: GlobalGracenote())
    globalCountLine: GlobalCountline = field(default_factory=lambda: GlobalCountline())
    globalSlur: GlobalSlur = field(default_factory=lambda: GlobalSlur())
    globalText: GlobalText = field(default_factory=lambda: GlobalText())
    globalBarLine: GlobalBarline = field(default_factory=lambda: GlobalBarline())
    globalBasegrid: GlobalBasegrid = field(default_factory=lambda: GlobalBasegrid())
    globalStave: GlobalStave = field(default_factory=lambda: GlobalStave())
    globalPage: GlobalPage = field(default_factory=lambda: GlobalPage())
    globalSection: GlobalSection = field(default_factory=lambda: GlobalSection())
    globalStartRepeat: GlobalStartRepeat = field(default_factory=lambda: GlobalStartRepeat())
    globalEndrepeat: GlobalEndRepeat = field(default_factory=lambda: GlobalEndRepeat())
    editorZoomPixelsQuarter: int = 100
    stopSignType: Literal['PianoTab', 'Klavarskribo'] = 'PianoTab'
    drawScale: float = 0.75