#!/usr/bin/env python3
'''
Verify that the embedded Courier New Bold font is being decoded and is usable
by PyMuPDF. Prints detailed diagnostics and writes a small PDF to
tools/output/font_check.pdf embedding the font. Skips Kivy to avoid crashes in
headless environments.

Safe to run standalone:
  .venv/bin/python tools/verify_fonts.py
'''
import os
import sys
import hashlib
from pathlib import Path

# Make workspace root importable when run from subfolder
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

print('Font verification: starting')

# 1) Resolve embedded font path
try:
    from utils.embedded_font import get_embedded_monospace_font
except Exception as e:
    print(f'ERROR: cannot import get_embedded_monospace_font: {e}')
    sys.exit(1)

font_path = None
try:
    font_path = get_embedded_monospace_font()
    print(f'embedded_font.get_embedded_monospace_font() -> {font_path}')
except Exception as e:
    print(f'ERROR: get_embedded_monospace_font failed: {e}')

# 2) Inspect path / family
exists = bool(font_path and isinstance(font_path, str) and os.path.exists(font_path))
print(f'is file path: {exists}')
if exists:
    size = os.path.getsize(font_path)
    sha1 = hashlib.sha1()
    with open(font_path, 'rb') as f:
        sha1.update(f.read())
    print(f'file size: {size} bytes')
    print(f'sha1: {sha1.hexdigest()}')
else:
    print('NOTE: result is not a file path. It may be a family name (e.g., 'Courier New').')

# 3) Try to load with PyMuPDF and embed in a tiny PDF
fitz = None
try:
    import fitz  # PyMuPDF
except Exception as e:
    print(f'WARNING: PyMuPDF not importable: {e}')

if fitz and exists:
    try:
        # Older PyMuPDF uses parameter name 'fontfile'
        fobj = fitz.Font(fontfile=font_path)
        print(f'PyMuPDF: successfully constructed fitz.Font(fontfile={os.path.basename(font_path)})')
    except Exception as e:
        print(f'PyMuPDF: FAILED to construct font from file: {e}')
        fobj = None

    try:
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        text = 'Courier New Bold 123 ABC xyz'
        if fobj is not None:
            # Use TextWriter with font object to guarantee usage of our TTF
            tw = fitz.TextWriter(page.rect)
            tw.append(fitz.Point(20, 60), text, font=fobj, fontsize=18)
            tw.write_text(page)
        else:
            # Fallback to page.insert_text with fontfile parameter
            page.insert_text(fitz.Point(20, 60), text, fontsize=18, fontfile=font_path, color=(0, 0, 0))
        outdir = ROOT / 'tools' / 'output'
        outdir.mkdir(parents=True, exist_ok=True)
        out_pdf = outdir / 'font_check.pdf'
        doc.save(out_pdf)
        doc.close()
        print(f'PDF: wrote {out_pdf}')
        # Reopen and list fonts used on page 0
        doc = fitz.open(out_pdf)
        page = doc[0]
        try:
            fonts = page.get_fonts(full=True)
        except Exception:
            fonts = page.get_fonts()
        print('PDF: page fonts:')
        for f in fonts:
            print('  - ', f)
        doc.close()
    except Exception as e:
        print(f'PDF: FAILED to create / inspect test PDF: {e}')

print('Font verification: done')
