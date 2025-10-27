from typing import List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class BaseGrid:
    numerator: int = 4
    denominator: int = 4
    gridTimes: List[float] = field(default_factory=lambda: [256.0, 512.0, 768.0])
    measureAmount: int = 8
    timeSignatureIndicatorVisible: bool = True
