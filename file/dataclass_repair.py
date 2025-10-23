from __future__ import annotations
from dataclasses import is_dataclass, fields, MISSING
from typing import Any, Set


def _default_for_field(f):
    if f.default is not MISSING:
        return f.default
    if getattr(f, "default_factory", MISSING) is not MISSING:  # type: ignore[attr-defined]
        return f.default_factory()  # type: ignore[misc]
    return None


def repair_missing_fields(obj: Any) -> Any:
    """
    Recursively ensure all dataclass fields exist on objects loaded from pickle
    by setting any missing attributes to their dataclass defaults.

    - Does NOT rename or prune attributes.
    - Safe to run on any object graph.
    """
    visited: Set[int] = set()

    def _visit(o: Any):
        oid = id(o)
        if oid in visited:
            return
        visited.add(oid)

        if is_dataclass(o):
            # Ensure declared fields exist
            for f in fields(o):
                if not hasattr(o, f.name):
                    setattr(o, f.name, _default_for_field(f))
            # Recurse into field values
            for f in fields(o):
                _visit(getattr(o, f.name, None))
        elif isinstance(o, dict):
            for v in o.values():
                _visit(v)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                _visit(v)
        # primitives: nothing

    _visit(obj)
    return obj
