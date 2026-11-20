#!/usr/bin/env python3
"""Viewer shots with explicit cameras and a contact sheet. Usage: vshot.py <out sheet png> <columns> [--tier id] name:clip:time:AZ:EL:DIST:TY [...]
AZ degrees from the creature's front (+z) toward its left (+x); EL degrees above; DIST metres from the target (0, TY, 0.1). Run from the repo root; output review/shots/."""
import math, subprocess, sys, json
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageDraw
P = Path('level_generation/creatures/mm9_banshee_claude')
args = sys.argv[1:]
sheet, cols = args[0], int(args[1]); args = args[2:]
tier = None
if args[0] == '--tier':
    tier = args[1]; args = args[2:]
m = json.load(open(P / 'review/viewer/manifest.json'))
url = f'http://127.0.0.1:8912/{P.as_posix()}/review/viewer/'
if tier:
    mo = next(x for x in m['models'] if x['id'] == tier)
    url += '#' + quote(json.dumps({'clip': 'Standing', 'model_sha256': mo['sha256']}))
specs = []; names = []
for a in args:
    n, clip, t, az, el, dist, ty = a.split(':')
    az, el, dist, ty = map(float, (az, el, dist, ty))
    tx = (0.0, ty, 0.1)
    cx = tx[0] + dist * math.cos(math.radians(el)) * math.sin(math.radians(az))
    cz = tx[2] + dist * math.cos(math.radians(el)) * math.cos(math.radians(az))
    cy = tx[1] + dist * math.sin(math.radians(el))
    specs.append(f'{n}:{clip}:{t}:front:body:{cx:.3f},{cy:.3f},{cz:.3f}:{tx[0]},{tx[1]},{tx[2]}'); names.append(n)
out = P / 'review/shots'
r = subprocess.run(['node', 'level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs', url, str(out), *specs], capture_output=True, text=True, timeout=580)
print(r.stdout[-200:], r.stderr[-300:])
ims = [Image.open(out / f'{n}.png').convert('RGB') for n in names]
w, h = 480, 354
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cols * w, rows * h))
for i, (im, n) in enumerate(zip(ims, names)):
    im = im.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 6), args[i].rsplit(':', 3)[0], fill=(255, 255, 0))
    s.paste(im, ((i % cols) * w, (i // cols) * h))
s.save(sheet)
print('SHEET', sheet, s.size)
