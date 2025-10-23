from pydantic import BaseModel, Field
import time

class Metainfo(BaseModel):
    appName: str = Field(default='PianoTab')
    extension: str = Field(default='.pianotab')
    description: str = Field(default='PianoTab score file')
    version: str = Field(default='1.0')
    created: str = Field(default_factory=lambda: time.strftime("%d-%m-%Y_%H:%M:%S"))
    author: str = Field(default='PianoTab Team')
    license: str = Field(default='MIT')