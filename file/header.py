from dataclasses import dataclass
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
    copyright: str = f'Copyright © {time.strftime("%Y")}, PianoTab. All rights reserved.'
    timeStamp: str = time.strftime("%d-%m-%Y_%H:%M:%S")
    genre: str = ''
    comment: str = ''
