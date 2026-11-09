#!/usr/bin/env python3
"""Face review sheet, orchestrator review r2 (viewer lighting): per tier one MM9 row (front, 3/4, profile; MM9 renders mirrored
to game handedness), one BEFORE row and one AFTER row (front close-up, 3/4, true profile, low 3/4, party view, and the front
close-up at 128 px blown back up). Shots: scripts/face_shots.sh before|after. Writes review/sheet_faces_r3.png."""
from PIL import Image, ImageDraw, ImageOps
S = 300
def tile(p, mirror=False, crop=None, small=False):
    im = Image.open(p).convert('RGB')
    if crop: im = im.crop(crop)
    if mirror: im = ImageOps.mirror(im)
    if small:
        k = 128 / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    k = S / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST if small else Image.LANCZOS)
    t = Image.new('RGB', (S, S), (90, 92, 98)); t.paste(im, ((S - im.width) // 2, (S - im.height) // 2)); return t
VC = (218, 0, 818, 763)
rows = []
for t, T in (('a', 'A (row 52)'), ('b', 'B (row 45)')):
    rows.append((f'MM9 {T}', [tile(f'references_hd/mm9/h{t}_{v}.png', True, (40, 0, 472, 400)) for v in ('front', 'q34', 'left')]))
    for st in ('r2', 'after'):
        cells = [tile(f'review/shots/{st}_pm3_{t}_{v}.png', False, VC) for v in ('front', 'q34', 'profile', 'low34', 'party')]
        cells.append(tile(f'review/shots/{st}_pm3_{t}_front.png', False, VC, small=True))
        rows.append((f'{st} {T}', cells))
img = Image.new('RGB', (6 * S, len(rows) * S), (40, 40, 40)); d = ImageDraw.Draw(img)
for i, (lab, cells) in enumerate(rows):
    for j, c in enumerate(cells): img.paste(c, (j * S, i * S))
    d.text((6, i * S + 6), lab, fill=(255, 255, 0))
img.save('review/sheet_faces_r3.png'); print('SHEET review/sheet_faces_r3.png', img.size)
