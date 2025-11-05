import fitz
import os

out_dir = os.path.join('tests','output')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir,'fitz_rotation_probe.pdf')

doc = fitz.open()
page = doc.new_page(width=595, height=420)  # A5-ish in pt

# Background
shape = page.new_shape()
shape.draw_rect(fitz.Rect(0,0,595,420))
shape.finish(fill=(1,1,1))
shape.commit()

angles = [0, 15, 30, 45, 60, 75, 90, 120, 150]
font_pt = 16
ax, ay = 100, 60
fontname = 'Courier-Bold'
font = fitz.Font(fontname)
for i, ang in enumerate(angles):
    y = ay + i*24
    txt = f'Angle {ang}'
    # Height = font size, width not needed for drawing baseline-left
    h = font_pt
    # Anchor: top-left at (ax, y)
    tlx, tly = ax, y
    blx, bly = tlx, tly + h

    color = (0,0,0)
    if ang:
        tw = fitz.TextWriter(page.rect)
        tw.append(fitz.Point(blx, bly), txt, font=font, fontsize=font_pt)
        m = fitz.Matrix(1,0,0,1,0,0).prerotate(-ang)
        tw.write_text(page, color=color, morph=(fitz.Point(ax, y), m))
    else:
        page.insert_text(fitz.Point(blx, bly), txt, fontname=fontname, fontsize=font_pt, color=color)

# Also try insert_text with rotate at baseline
page.insert_text(fitz.Point(300, 60+9*24), 'rotate param 90', fontsize=16, fontname=fontname, color=(1,0,0), rotate=90)


doc.save(out_path)
print('WROTE', out_path)
