from pydantic import BaseModel, Field
import time

class Header(BaseModel):
    title: str = Field(default='Untitled')
    subtitle: str = Field(default='')
    composer: str = Field(default='')
    arranger: str = Field(default='')
    lyricist: str = Field(default='')
    publisher: str = Field(default='')
    copyright: str = Field(default_factory=lambda: f'Copyright © {time.strftime("%Y")}, PianoTab. All rights reserved.')
    timeStamp: str = Field(default_factory=lambda: time.strftime("%d-%m-%Y_%H:%M:%S"))
    genre: str = Field(default='')
    comment: str = Field(default='')
