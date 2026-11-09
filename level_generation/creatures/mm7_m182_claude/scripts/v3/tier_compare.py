"""Tier comparison sheet (review): for each tier a Blender preview (scripts/v3/preview_tex.py on the baked tier maps,
Standing frame 0, view 1 of the motion camera: front three-quarter) next to the native m182 frame in that tier's
palette. Usage: tier_compare.py <out.png> [frame=m182sa1]  (renders into work/v3/renders/tiers_cmp/)"""
import json, subprocess, sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(P / 'scripts'))
import os
REPO = P.parents[2]
def native(frame, pid, SIZE=320):
    sprites = REPO / 'assets_dev/engine/sprites'; listing = {e.lower(): e for e in os.listdir(sprites)}
    ids = np.asarray(Image.open(sprites / listing[frame + '.bmp']))
    palette = np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    rgb = palette[ids].copy(); rgb[ids == 0] = (85, 88, 91); rows, cols = np.nonzero(ids)
    im = Image.fromarray(rgb).crop((max(cols.min() - 8, 0), max(rows.min() - 8, 0), cols.max() + 8, rows.max() + 8))
    f = SIZE / max(im.size); return im.resize((int(im.width * f), int(im.height * f)), Image.NEAREST)
out = Path(sys.argv[1]); frame = sys.argv[2] if len(sys.argv) > 2 else 'm182sa1'
R = P / 'work/v3/renders/tiers_cmp'; R.mkdir(parents=True, exist_ok=True)
spec = {'out': str(R), 'res': [900, 900], 'shots': [
    {'name': 'q', 'clip': 'Standing', 'frame': 0, 'dir': [0.70710678, -0.70710678, 0.0195], 'target': [0, -0.45, 0.85], 'scale': 3.3},
    {'name': 'side', 'clip': 'Standing', 'frame': 0, 'dir': [1, 0, 0.0195], 'target': [0, -0.4, 0.85], 'scale': 3.3}]}
(R / 'spec.json').write_text(json.dumps(spec))
cells = []
for tier, pid in zip('abc', (183, 184, 185)):
    for v in ('q', 'side'):
        pass
    subprocess.run(['blender', '-b', '--factory-startup', '-P', str(P / 'scripts/v3/preview_tex.py'), '--',
                    *(str(P / f'work/v3/tiers/{s}_{tier}.png') for s in ('body', 'head', 'wings')), str(R / 'spec.json')],
                   check=True, capture_output=True)
    row = [Image.open(R / 'q.png').convert('RGB').resize((320, 320)), native(frame, pid).convert('RGB'),
           Image.open(R / 'side.png').convert('RGB').resize((320, 320)), native('m182sa2', pid).convert('RGB')]
    cells.append((tier, pid, row))
sheet = Image.new('RGB', (4 * 330, len(cells) * 345), (60, 60, 64)); d = ImageDraw.Draw(sheet)
for r, (tier, pid, row) in enumerate(cells):
    for c, im in enumerate(row):
        sheet.paste(im, (c * 330 + (320 - im.width) // 2, r * 345 + 22 + (320 - im.height) // 2))
    d.text((6, r * 345 + 4), f'tier {tier.upper()} (palette {pid}): v3 model | native {frame} | v3 side | native m182sa2', fill=(255, 255, 160))
sheet.save(out); print('TIER_SHEET', out)
