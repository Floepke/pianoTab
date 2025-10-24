"""
Helpers for inheritable fields that resolve from SCORE global properties.

Two utilities are provided:
- InheritMixin: centralizes the "None means inherit" behavior using __getattribute__ and __setattr__.
- inherit_property: legacy helper kept for compatibility with earlier versions.
"""

from typing import Any


class InheritMixin:
    """Mixin that implements dynamic inheritance for Pydantic models.

    Requirements on the model using this mixin:
    - Provide a class attribute `_INHERIT_CONFIG`: dict[str, tuple[str, str, Any]]
      Mapping public attribute name -> (private_field_name, inherit_path, default_value)
      Example: { 'color': ('_color', 'properties.globalNote.color', '#000000') }
    - Have a `score` attribute pointing to the SCORE instance (excluded from JSON).
    - Store inheritable values in private fields (e.g., `_color`) with alias set to the public name
      so JSON uses the public names.
    """

    _INHERIT_CONFIG: dict[str, tuple[str, str, Any]] = {}

    def set_score_reference(self, score: Any) -> None:
        """Set the score reference without triggering Pydantic validation."""
        object.__setattr__(self, "score", score)

    @staticmethod
    def _resolve_path(root: Any, path: str, default: Any) -> Any:
        obj = root
        for attr in path.split('.'):
            obj = getattr(obj, attr, None)
            if obj is None:
                return default
        return obj

    def __getattribute__(self, name: str):  # type: ignore[override]
        # Fast-path for private/special attributes
        if name.startswith('_') or name in (
            '__dict__', '__class__', 'set_score_reference', '_resolve_path', '_INHERIT_CONFIG'
        ):
            return object.__getattribute__(self, name)

        # Config-driven inheritable fields
        try:
            cfg = object.__getattribute__(self, '_INHERIT_CONFIG')
        except Exception:
            cfg = {}

        if name in cfg:
            private_name, inherit_path, default = cfg[name]
            try:
                raw = object.__getattribute__(self, private_name)
            except AttributeError:
                raw = None
            if raw is not None:
                return raw
            # Inherit from score
            score = getattr(self, 'score', None)
            if score is None:
                return default
            return self._resolve_path(score, inherit_path, default)

        # Non-inheritable attribute
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:  # type: ignore[override]
        # Private/special attributes go straight through
        if name.startswith('_') or name == 'score':
            object.__setattr__(self, name, value)
            return

        # Redirect public inheritable names to private storage
        try:
            cfg = object.__getattribute__(self, '_INHERIT_CONFIG')
        except Exception:
            cfg = {}

        if name in cfg:
            private_name = cfg[name][0]
            object.__setattr__(self, private_name, value)
            return

        # Everything else
        object.__setattr__(self, name, value)


def inherit_property(field_name: str, inherit_path: str, default: Any = None) -> property:
    """Legacy helper retained for compatibility with older code paths.

    Prefer using InheritMixin with _INHERIT_CONFIG over this property-based approach.
    """
    private_name = field_name if field_name.startswith('_') else f'_{field_name}'

    def getter(self) -> Any:
        value = getattr(self, private_name, None)
        if value is not None:
            return value
        score = getattr(self, 'score', None)
        if score is None:
            return default
        obj = score
        for attr in inherit_path.split('.'):
            obj = getattr(obj, attr, None)
            if obj is None:
                return default
        return obj

    def setter(self, value: Any):
        setattr(self, private_name, value)

    return property(getter, setter)
