from dataclasses import dataclass
import time

@dataclass
class Metainfo:
    appName: str = 'PianoTab'
    extension: str = '.pianotab'
    description: str = 'PianoTab score file'
    version: str = '1.0'
    created: str = time.strftime("%d-%m-%Y_%H:%M:%S")
    author: str = 'PianoTab Team'
    license: str = 'MIT'