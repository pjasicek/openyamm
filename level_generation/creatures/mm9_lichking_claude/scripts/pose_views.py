"""Numpy-skinned poses -> Blender clay views (the glTF importer's bind guess is not trusted for A-pose binds). Args: <glb> <out png> <items clip:t,...> <views front:left:q34...> ; env CENTER x,y,z (Blender frame, default pelvis) ORTHO SIZE"""
import sys, subprocess, os, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from PIL import Image, ImageDraw
glb, out, items, views = sys.argv[1:5]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
SIZE = os.environ.get('SIZE', '420'); ORTHO = os.environ.get('ORTHO', '2.4')
rows = []
tri0 = None
wdir = HERE / 'work/_pv'; wdir.mkdir(exist_ok=True)
for k, it in enumerate(items.split(',')):
    clip, t = it.split(':')
    w = m.world(m.sample(clip, float(t)))
    Rs = m.skinned_positions(w)
    # LOD0 primitives only
    P = []; T = []; o = 0; C = []
    for pi, (p, tr) in enumerate(Rs):
        if pi >= len(m.primitives): break
        P.append(p); T.append(np.asarray(tr).reshape(-1, 3) + o); o += len(p)
    P = np.vstack(P); T = np.vstack(T)
    co = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
    np.savez(wdir / f'p{k}.npz', co=co, tri=T)
    pel = w[names.index('Bip01 Pelvis')][:3, 3]
    c = os.environ.get('CENTER') or f'{pel[0]},{-pel[2]},{max(0.95, pel[1])}'
    rows.append((it, k, c))
REPO = HERE.parents[2]
tok = open(HERE / 'work/token').read().strip()
for it, k, c in rows:
    subprocess.run(['tools/run_creature_blender.sh', '--token', tok, 'level_generation/creatures/mm9_lichking_claude/scripts/view_npz.py', str(wdir / f'p{k}.npz'), str(wdir / f'v{k}'), c, ORTHO, SIZE, views], cwd=REPO, capture_output=True)
vs = [v.split('=')[0] for v in views.split(':')]
s = int(SIZE); W = Image.new('RGB', (s * len(vs), s * len(rows)))
for y, (it, k, c) in enumerate(rows):
    for x, v in enumerate(vs):
        im = Image.open(wdir / f'v{k}_{v}.png').convert('RGB'); ImageDraw.Draw(im).text((4, 4), f'{it} {v}', fill=(255, 255, 0)); W.paste(im, (x * s, y * s))
W.save(out)
