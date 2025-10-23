from dataclasses import dataclass
import time

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
