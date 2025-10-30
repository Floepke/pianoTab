from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import time

@dataclass_json
@dataclass
class MetaInfo:
    appName: str = 'PianoTab'
    extension: str = '.piano'
    description: str = 'PianoTab score file'
    version: str = '1.0'
    created: str = field(default_factory=lambda: time.strftime("%d-%m-%Y_%H:%M:%S"))
    author: str = 'PianoTab Team'
    license: str = 'MIT'