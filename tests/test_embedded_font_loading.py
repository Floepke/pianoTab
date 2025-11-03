import os
import pytest

from utils.embedded_font import get_embedded_monospace_font


def test_embedded_font_returns_value():
    path = get_embedded_monospace_font()
    assert isinstance(path, str)


def test_embedded_font_file_or_family(monkeypatch):
    path = get_embedded_monospace_font()
    # Either a real .ttf path that exists, or a family name (fallback)
    if os.path.exists(path):
        assert path.lower().endswith('.ttf'), f"Expected a TTF file path, got: {path}"
        size = os.path.getsize(path)
        assert size > 10000, f"Embedded font file seems too small: {size} bytes"
    else:
        # Family name fallback - non-strict assertion, but still informative
        assert 'courier' in path.lower(), f"Expected a courier family name, got: {path}"


def test_pymupdf_can_load_font_if_file_present():
    path = get_embedded_monospace_font()
    try:
        import fitz
    except Exception:
        pytest.skip("PyMuPDF (fitz) not available in environment")
    if not os.path.exists(path):
        pytest.skip("Embedded font path is not a file; likely a family name fallback")
    # Should be able to construct a Font from the TTF path
    fobj = fitz.Font(file=path)
    assert fobj is not None
