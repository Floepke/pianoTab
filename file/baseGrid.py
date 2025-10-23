from typing import List
from pydantic import BaseModel, Field

class BaseGrid(BaseModel):
    numerator: int = Field(default=4)
    denominator: int = Field(default=4)
    gridTimes: List[float] = Field(default_factory=lambda: [256.0, 512.0, 768.0])
    measureAmount: int = Field(default=8)
    timeSignatureIndicatorVisible: bool = Field(default=True)
