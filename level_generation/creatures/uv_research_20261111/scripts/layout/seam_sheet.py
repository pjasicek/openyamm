#!/usr/bin/env python3
"""Seam review sheet: for each trial, the seam texture (seam_texture.py) rendered on its upload GLB from front, side,
back and above (render_views.py, same cameras), one row per trial with its seam numbers.

    seam_sheet.py <trial dir> <out png> <name>... [--yaw 90] [--crop 0.15]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('dir')
parser.add_argument('out')
parser.add_argument('names', nargs='+')
parser.add_argument('--yaw', default='90')
parser.add_argument('--crop', type=float, default=0.12)
parser.add_argument('--res', type=int, default=900)
args = parser.parse_args()
d = Path(args.dir).resolve()
rows = []
for name in args.names:
    tex = d / f'{name}_seamtex.png'
    subprocess.run([sys.executable, str(HERE / 'seam_texture.py'), str(d / f'{name}_faces.npz'), str(tex), '--width', '9'],
                   check=True)
    subprocess.run([str(HERE / 'blender.sh'), str(HERE / 'render_views.py'), str(d / 'render.log'),
                    str(d / f'{name}_upload.glb'), str(tex), str(d / f'r_{name}'), f'yaw={args.yaw}',
                    f'res={args.res}'], check=True)
    r = json.loads((d / f'{name}_report.json').read_text())['seams']
    ims = []
    for v in ('front', 'side', 'back', 'above'):
        im = Image.open(d / f'r_{name}_{v}.png').convert('RGB')
        c = int(args.res * args.crop)
        im = im.crop((c, c, args.res - c, args.res - c))
        ImageDraw.Draw(im).text((8, 8), f'{name}  {v}', fill=(255, 255, 255))
        ims.append(im)
    ImageDraw.Draw(ims[0]).text((8, 24), f"seam {r['total_len']}  vis-weighted {r['vis_weighted_len']}  exposed "
                                         f"{r['exposed_len']}", fill=(255, 255, 160))
    rows.append(ims)
w, h = rows[0][0].size
sheet = Image.new('RGB', (w * 4, h * len(rows)))
for i, ims in enumerate(rows):
    for j, im in enumerate(ims):
        sheet.paste(im, (j * w, i * h))
sheet.save(args.out)
print('sheet', args.out)
