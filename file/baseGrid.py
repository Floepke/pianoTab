from typing import List
from dataclasses_json import dataclass_json
from dataclasses import dataclass, field

@dataclass_json
@dataclass
class Basegrid:
    numerator: int = 4
    denominator: int = 4
    gridTimes: List[float] = field(
        default_factory=lambda: [256.0, 512.0, 768.0]
    )
    measureAmount: int = 8
    timeSignatureIndicatorVisible: bool = True
