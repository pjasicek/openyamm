#!/usr/bin/env python3
"""Close-up viewer shots at joints, as one labelled sheet. Usage (repo root): closeups.py <project> <token> <tier> <glb> <out png>
<name|clip|seconds|joint|ox,oy,oz|dist> ...   Offsets are GLB axes (glTF +Y up, nose +Z)."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from urllib.parse import quote
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
proj, token, tier, glb, out = sys.argv[1:6]
m = Model(Glb(glb))
names = [n.get('name') for n in m.glb.json['nodes']]
args = [l.strip() for a in sys.argv[6:] for l in (open(a[1:]).read().splitlines() if a.startswith('@') else [a]) if l.strip()]
items = [a.split('|') for a in args]
spec = []
for name, clip, sec, joint, off, dist in items:
    w = m.world(m.sample(clip, float(sec)))
    p = w[names.index(joint)][:3, 3]
    o = np.array([float(x) for x in off.split(',')])
    o = o / np.linalg.norm(o) * float(dist)
    spec.append(f'cl_{tier}_{name}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
man = json.loads((Path(proj) / 'review/viewer/manifest.json').read_text())
sha = next(x for x in man['models'] if x['id'] == tier)['sha256']
url = f'http://127.0.0.1:8912/{proj}/review/viewer/#' + quote(json.dumps({'clip': man['default_clip'], 'model_sha256': sha}))
# the review wrapper accepts five fields only; viewer_shots.mjs itself takes a camera and a target (as mm9_skeletonwarrior_claude does)
subprocess.run(['node', 'level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs', url, str((Path(proj) / 'review/shots').resolve()), *spec], check=True, stdout=subprocess.DEVNULL)
T = 760
cols = 5
rows = (len(items) + cols - 1) // cols
S = Image.new('RGB', (T * cols, T * rows), (30, 30, 30))
d = ImageDraw.Draw(S)
for i, (name, clip, sec, joint, off, dist) in enumerate(items):
    im = Image.open(Path(proj) / f'review/shots/cl_{tier}_{name}.png').convert('RGB')
    W, H = im.size
    im = im.crop(((W - H) // 2, 20, (W + H) // 2, H + 20 - 40)).resize((T, T), Image.LANCZOS)
    S.paste(im, ((i % cols) * T, (i // cols) * T))
    d.rectangle([(i % cols) * T, (i // cols) * T, (i % cols) * T + 270, (i // cols) * T + 16], fill=(0, 0, 0))
    d.text(((i % cols) * T + 4, (i // cols) * T + 2), f'{name} {clip} {sec} {joint}', fill=(255, 255, 120))
S.save(out)
print('CLOSE', out, S.size)
