from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import time

@dataclass_json
@dataclass
class Header:
    title: str = 'Untitled'
    subtitle: str = ''
    composer: str = ''
    arranger: str = ''
    lyricist: str = ''
    publisher: str = ''
    copyright: str = field(default_factory=lambda: f'Copyright © {time.strftime("%Y")}, PianoTab. All rights reserved.')
    timeStamp: str = field(default_factory=lambda: time.strftime("%d-%m-%Y_%H:%M:%S"))
    genre: str = ''
    comment: str = ''
