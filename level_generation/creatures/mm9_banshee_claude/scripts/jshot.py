#!/usr/bin/env python3
"""Viewer shots framed on a joint: the target is the joint's world position at that clip time in the runtime GLB, so a close-up always frames what it names (the mummy's sit and dead close-ups cut theirs off).
Usage (repo root): jshot.py <out sheet png> <columns> --tier id name:clip:time:joint:AZ:EL:DIST [...]  AZ from the creature's front (+z) toward its left (+x). Output review/shots/."""
import json, math, subprocess, sys
from pathlib import Path
from urllib.parse import quote
import numpy as np
from PIL import Image, ImageDraw
P = Path('level_generation/creatures/mm9_banshee_claude')
sys.path.insert(0, 'level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
args = sys.argv[1:]
sheet, cols = args[0], int(args[1]); args = args[2:]
tier = None
if args[0] == '--tier':
    tier = args[1]; args = args[2:]
m = Model(Glb(P / 'export/mm9_banshee.glb'))
doc = m.glb.json
nid = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
vm = json.load(open(P / 'review/viewer/manifest.json'))
url = f'http://127.0.0.1:8912/{P.as_posix()}/review/viewer/'
if tier:
    mo = next(x for x in vm['models'] if x['id'] == tier)
    url += '#' + quote(json.dumps({'clip': 'Standing', 'model_sha256': mo['sha256']}))
specs = []; names = []; labels = []
for a in args:
    n, clip, t, joint, az, el, dist = a.split(':')
    az, el, dist = float(az), float(el), float(dist)
    w = m.world(m.sample(clip, float(t)))
    tx = w[nid[joint]][:3, 3]
    if joint.endswith('+'):
        pass
    cx = tx[0] + dist * math.cos(math.radians(el)) * math.sin(math.radians(az))
    cz = tx[2] + dist * math.cos(math.radians(el)) * math.cos(math.radians(az))
    cy = tx[1] + dist * math.sin(math.radians(el))
    specs.append(f'{n}:{clip}:{t}:front:body:{cx:.3f},{cy:.3f},{cz:.3f}:{tx[0]:.3f},{tx[1]:.3f},{tx[2]:.3f}'); names.append(n); labels.append(f'{clip} {t} {joint} az{az:.0f} el{el:.0f}')
out = P / 'review/shots'
r = subprocess.run(['node', 'level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs', url, str(out), *specs], capture_output=True, text=True, timeout=580)
print(r.stdout[-120:], r.stderr[-300:])
ims = [Image.open(out / f'{n}.png').convert('RGB') for n in names]
w_, h = 480, 354
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cols * w_, rows * h))
for i, (im, lb) in enumerate(zip(ims, labels)):
    im = im.resize((w_, h), Image.LANCZOS)
    ImageDraw.Draw(im).text((6, 6), lb, fill=(255, 255, 0))
    s.paste(im, ((i % cols) * w_, (i // cols) * h))
s.save(sheet)
print('SHEET', sheet, s.size)
