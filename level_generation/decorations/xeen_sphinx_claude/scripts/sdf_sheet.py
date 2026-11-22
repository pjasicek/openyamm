"""Combine the SDF previews (front | side over top) into one sheet. Usage: sdf_sheet.py <id>"""
import sys
from PIL import Image
w = f'work/{sys.argv[1]}/sdf'
fr, sd, tp = (Image.open(f'{w}_{v}.png') for v in ('front', 'side', 'top'))
H = 420
def sc(im, h): return im.resize((max(1, int(im.size[0] * h / im.size[1])), h))
fr, sd = sc(fr, H), sc(sd, H)
tp = tp.rotate(90, expand=True)
tp = tp.resize((sd.size[0], int(tp.size[1] * sd.size[0] / tp.size[0])))
s = Image.new('L', (fr.size[0] + sd.size[0] + 10, H + tp.size[1] + 10), 40)
s.paste(fr, (0, 0)); s.paste(sd, (fr.size[0] + 10, 0)); s.paste(tp, (fr.size[0] + 10, H + 10))
s.save(f'{w}_sheet.png')
