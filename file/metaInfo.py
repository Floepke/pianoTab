from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import time

@dataclass_json
@dataclass
class MetaInfo:
    appName: str = 'pianoTAB'
    extension: str = '.piano'
    description: str = 'pianoTAB score file'
    version: str = '1.0'
    created: str = field(default_factory=lambda: time.strftime('%d-%m-%Y_%H:%M:%S'))
    author: str = 'pianoTAB Team'
    license: str = 'MIT'