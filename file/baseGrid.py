from typing import List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

@dataclass_json
@dataclass
class BaseGrid:
    numerator: int = field(default=4, metadata=config(field_name='numerator'))
    denominator: int = field(default=4, metadata=config(field_name='denominator'))
    gridTimes: List[float] = field(default_factory=lambda: [256.0, 512.0, 768.0])
    measureAmount: int = field(default=8, metadata=config(field_name='measureAmount'))
    timeSignatureIndicatorVisible: int = field(default=1, metadata=config(field_name='timeSignatureIndicatorVisible?')) # ? means bool 1 = visible, 0 = hidden
