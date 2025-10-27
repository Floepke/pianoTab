# When to Use `field()` in Dataclasses

## TL;DR: Use `field()` when you need special behavior

```python
from dataclasses import dataclass, field

@dataclass
class Example:
    # ✅ Simple values - NO field() needed
    name: str = "default"
    age: int = 0
    active: bool = True
    
    # ✅ MUST use field() for mutable defaults (lists, dicts, sets)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ✅ Use field() for special options
    internal_id: int = field(default=0, repr=False, compare=False)
    computed: str = field(init=False, default="computed")
```

## Detailed Rules

### ✅ **MUST use `field()` for mutable defaults**

```python
# ❌ WRONG - All instances share the same list!
class BadExample:
    items: List[str] = []  # Dangerous!

# ✅ CORRECT - Each instance gets its own list
class GoodExample:
    items: List[str] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
```

**Why?** Mutable defaults are evaluated once at class definition time, so all instances share the same object.

### ✅ **Use `field()` when you need special options**

```python
@dataclass
class Note:
    id: int = 0
    
    # Don't show in repr
    _score: Optional['SCORE'] = field(default=None, repr=False)
    
    # Don't compare in equality checks
    cached_data: Dict = field(default_factory=dict, compare=False)
    
    # Don't include in __init__
    computed_value: str = field(init=False, default="")
    
    # Custom factory function
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))
```

**Field options:**
- `default`: Default value
- `default_factory`: Function that returns default value
- `repr`: Include in `repr()` (default: True)
- `compare`: Include in equality comparison (default: True)
- `hash`: Include in hash (default: None)
- `init`: Include in `__init__()` (default: True)
- `metadata`: Dict of metadata (for tools)

### ❌ **DON'T use `field()` for simple immutable defaults**

```python
# ❌ Unnecessary - adds complexity
class OverEngineered:
    name: str = field(default="default")
    age: int = field(default=0)

# ✅ Clean and simple
class Clean:
    name: str = "default"
    age: int = 0
```

## Best Practices for PianoTab

```python
@dataclass_json
@dataclass
class Note:
    # Simple values - no field()
    id: int = 0
    time: float = 0.0
    pitch: int = 40
    velocity: int = 80
    hand: Literal['<', '>'] = '>'
    
    # Mutable defaults - MUST use field()
    articulation: List[Articulation] = field(default_factory=list)
    
    # Inherited properties - no field() (None is immutable)
    color: Optional[str] = None
    colorMidiNote: Optional[str] = None
    blackNoteDirection: Optional[Literal['^', 'v']] = None
```

## Summary

| Case | Use `field()`? | Example |
|------|----------------|---------|
| Immutable default (int, str, bool, None) | ❌ No | `age: int = 0` |
| Mutable default (list, dict, set) | ✅ Yes | `items: List = field(default_factory=list)` |
| Custom factory function | ✅ Yes | `id: int = field(default_factory=uuid4)` |
| Special options (repr, compare, init) | ✅ Yes | `_internal: Any = field(repr=False)` |
| Computed/derived values | ✅ Yes | `total: int = field(init=False)` |

**Rule of thumb:** If you just need a simple default value and it's immutable, don't use `field()`. Only use it when you need mutable defaults or special behavior.
