import os
import sys

# Ensure repository root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.pymupdfexport import PyMuPDFCanvas

def main():
    out_dir = os.path.join('tests','output')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,'pdf_rotation_debug.pdf')

    cv = PyMuPDFCanvas(pdf_mode=True, width_mm=210.0, height_mm=148.0)
    page = cv.new_page()

    cv.debug_pdf_text = True

    # Draw reference axes
    for x in range(10, 200, 10):
        cv.add_line(x, 5, x, 140, stroke_color='#eeeeee', stroke_width_mm=0.2)
    for y in range(5, 140, 10):
        cv.add_line(10, y, 200, y, stroke_color='#eeeeee', stroke_width_mm=0.2)

    angles = [0, 15, 30, 45, 60, 75, 90, 120, 150]
    y = 15
    for ang in angles:
        cv.add_text(f'Angle {ang}', 20, y, 16, angle_deg=ang, anchor='top_left', color='#000000')
        y += 12

    cv.save_pdf(out_path)
    print('WROTE', out_path)

if __name__ == '__main__':
    main()
