#!/usr/bin/env python3
"""Installed vs reduced viewer shots, framed on a joint (as mm9_banshee_claude/scripts/jshot.py), one comparison sheet:
each row is one shot, columns installed | reduced | |difference| x 4. Same viewer, same camera, same clip time.
Usage (repo root): cshot.py <out sheet png> <tier a|b|c> <reduced suffix> name:clip:time:joint:AZ:EL:DIST [...]
AZ from the creature's front (+z) toward its left (+x). Shots go to review/shots/<tier>_<model>_<name>.png."""
import json, math, subprocess, sys
from pathlib import Path
from urllib.parse import quote
import numpy as np
from PIL import Image, ImageDraw, ImageChops
P = Path('level_generation/creatures/mm9_banshee_reduce_claude')
sys.path.insert(0, 'level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model  # noqa: E402
sheet, tier, red = sys.argv[1:4]; args = sys.argv[4:]
m = Model(Glb('assets_source/worlds/mm9/models/mm9_banshee.glb'))     # clips and skeleton are identical in both files
nid = {n.get('name'): i for i, n in enumerate(m.glb.json['nodes'])}
vm = json.load(open(P / 'review/viewer/manifest.json'))
base = f'http://127.0.0.1:8912/{P.as_posix()}/review/viewer/'
specs, labels = [], []
for a in args:
    n, clip, t, joint, az, el, dist = a.split(':')
    az, el, dist = float(az), float(el), float(dist)
    tx = m.world(m.sample(clip, float(t)))[nid[joint]][:3, 3]
    cx = tx[0] + dist * math.cos(math.radians(el)) * math.sin(math.radians(az))
    cz = tx[2] + dist * math.cos(math.radians(el)) * math.cos(math.radians(az))
    cy = tx[1] + dist * math.sin(math.radians(el))
    specs.append((n, f'{clip}:{t}:front:body:{cx:.3f},{cy:.3f},{cz:.3f}:{tx[0]:.3f},{tx[1]:.3f},{tx[2]:.3f}'))
    labels.append(f'{clip} {t} {joint} az{az:.0f} el{el:.0f} d{dist}')
out = P / 'review/shots'
for model in ('installed', red):
    mo = next(x for x in vm['models'] if x['id'] == f'banshee_{tier}_{model}')
    url = base + '#' + quote(json.dumps({'clip': 'Standing', 'model_sha256': mo['sha256']}))
    r = subprocess.run(['node', 'level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs', url, str(out),
                        *[f'{tier}_{model}_{n}:{s}' for n, s in specs]], capture_output=True, text=True, timeout=900)
    if r.returncode:
        print(r.stdout[-300:], r.stderr[-600:]); sys.exit(1)
w, h = 520, 384
s = Image.new('RGB', (3 * w, len(specs) * h), (20, 20, 20))
d = ImageDraw.Draw(s)
for i, ((n, _), lb) in enumerate(zip(specs, labels)):
    a = Image.open(out / f'{tier}_installed_{n}.png').convert('RGB').resize((w, h), Image.LANCZOS)
    b = Image.open(out / f'{tier}_{red}_{n}.png').convert('RGB').resize((w, h), Image.LANCZOS)
    diff = np.asarray(ImageChops.difference(a, b), np.float32)
    dm = Image.fromarray(np.clip(diff * 4, 0, 255).astype(np.uint8))
    for j, im in enumerate((a, b, dm)):
        s.paste(im, (j * w, i * h))
    d.text((6, i * h + 6), f'{tier} installed  {lb}', fill=(255, 255, 0))
    d.text((w + 6, i * h + 6), f'{tier} reduced {red}', fill=(120, 255, 120))
    d.text((2 * w + 6, i * h + 6), f'|diff| x4  mean {diff.mean():.2f}', fill=(255, 160, 160))
s.save(sheet)
print('SHEET', sheet, s.size)
