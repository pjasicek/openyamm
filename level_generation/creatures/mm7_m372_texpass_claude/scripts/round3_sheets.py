"""Round 3 review sheets (identical cameras):
- review/round3_robe_sheet.png: HD masters (front, left, right, three-quarter), then the face follow-up install (r2)
  and round 3 (r3), skin AA: Standing front, left, right, 3/4, Walk2 mid-step front, left, 3/4, hip close-ups.
- review/round3_face_sheet.png: every skin, r2 against r3, face close-up front, 3/4 and side.
Usage: round3_sheets.py"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
CELL = 300


def fit(im, box=None):
    im = im.convert('RGB')
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    im.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
    return im


def sheet(rows, out, label_w=110):
    cols = max(len(r[1]) for r in rows)
    img = Image.new('RGB', (label_w + cols * CELL, len(rows) * CELL), (24, 26, 30))
    d = ImageDraw.Draw(img)
    for r, (label, ims) in enumerate(rows):
        d.text((4, r * CELL + CELL // 2), label, fill=(235, 235, 235))
        for c, im in enumerate(ims):
            img.paste(im, (label_w + c * CELL + (CELL - im.width) // 2, r * CELL + (CELL - im.height) // 2))
    img.save(out)
    print('SHEET', out, img.size)


body = (0.3, 0.05, 0.7, 0.98)
hd = HERE / 'references_hd'
rows = [('HD masters', [fit(Image.open(hd / f)) for f in ('01_front.png', '03_left.png', '04_right.png',
                                                           '00_three_quarter.png')])]
for v, label in (('r2', 'face follow-up\n(installed)'), ('r3', 'round 3')):
    names = ['std_front', 'std_left', 'std_right', 'std_q', 'walk_front', 'walk_left', 'walk_q']
    ims = [fit(Image.open(S / f'robe_{v}_{n}.png'), body) for n in names]
    ims += [fit(Image.open(S / f'robe_{v}_{n}.png'), (0.15, 0.0, 0.85, 1.0)) for n in ('hip_q', 'hip_right')]
    rows.append((label, ims))
sheet(rows, HERE / 'review' / 'round3_robe_sheet.png')
rows = []
for k in ('aa', 'ab', 'ac', 'ba', 'bb', 'bc'):
    for v, label in (('r2', 'follow-up'), ('r3', 'round 3')):
        rows.append((f'm372_{k}\n{label}', [fit(Image.open(S / f'{k}_{v}_{n}.png'), (0.15, 0.0, 0.85, 0.75))
                                           for n in ('cf', 'cq', 'cs')]))
sheet(rows, HERE / 'review' / 'round3_face_sheet.png')
