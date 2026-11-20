"""Tile a face_shots.sh directory (+ MM9 front/profile and a 128 px party-view head) into one sheet.
Args: <shot dir> <mm9 render dir> <out png>"""
import sys
from PIL import Image, ImageDraw
d, m, out = sys.argv[1:4]
C = 360
rows = []
for clip in ('Standing', 'Talk'):
    row = []
    for v in ('front', 'q34', 'profR', 'profL', 'low'):
        im = Image.open(f'{d}/{clip}_{v}.png').convert('RGB'); w, h = im.size; s = min(w, h)
        row.append((im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((C, C), Image.LANCZOS), f'{clip} {v}'))
    p = Image.open(f'{d}/{clip}_party.png').convert('RGB'); w, h = p.size; s = min(w, h)
    p = p.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
    row.append((p.resize((C, C), Image.LANCZOS), f'{clip} party'))
    q = Image.open(f'{d}/{clip}_partyhead.png').convert('RGB'); w2, h2 = q.size; s2 = min(w2, h2)
    k = int(s2 * 0.32); q = q.crop(((w2 - k) // 2, (h2 - k) // 2 - k // 3, (w2 + k) // 2, (h2 + k) // 2 - k // 3))
    hd = q.resize((128, 128), Image.LANCZOS).resize((C, C), Image.NEAREST)
    row.append((hd, f'{clip} party-distance head @128px'))
    rows.append(row)
mm = [(Image.open(f'{m}/head_{v}.png').convert('RGB').resize((C, C)), f'MM9 {v}') for v in ('front', 'q34', 'left', 'right')]
rows.append(mm)
S = Image.new('RGB', (C * 7, C * len(rows)), (40, 40, 40)); dr = ImageDraw.Draw(S)
for r, row in enumerate(rows):
    for c, (im, lab) in enumerate(row):
        S.paste(im, (c * C, r * C)); dr.text((c * C + 5, r * C + 5), lab, fill=(255, 255, 0))
S.save(out); print('FACE_SHEET', out)
