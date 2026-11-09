#!/usr/bin/env python3
"""Rest-pose painter's render of the installed LOD0 faces coloured by a per-face label (front / left side / back), PIL only.
Usage: part_plot.py <out.png> [ymin] [label npy (per GLB face) | part]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_dookmilitia.glb')))
tri = np.vstack([np.asarray(p['positions'])[np.asarray(p['triangles'])] for p in m.primitives])
g = np.load(HERE / 'work' / 'glb_parts.npz')
lab = g['part'] if len(sys.argv) < 4 or sys.argv[3] == 'part' else np.load(sys.argv[3]).astype(int)
ymin = float(sys.argv[2]) if len(sys.argv) > 2 else -9
sel = tri[:, :, 1].max(1) > ymin; tri = tri[sel]; lab = lab[sel]
rng = np.random.default_rng(3); ids = sorted(np.unique(lab))
pal = {p: tuple(int(c) for c in rng.integers(40, 255, 3)) for p in ids}
pal.update({0: (230, 60, 60)} if 0 in pal else {})
H = 900; panels = []
lo = tri.reshape(-1, 3).min(0); hi = tri.reshape(-1, 3).max(0); s = (H - 40) / (hi[1] - lo[1])
for u, sgn, dep, dsg in [(0, -1, 2, 1), (2, 1, 0, 1), (0, 1, 2, -1)]:   # glTF: figure faces +z; front view looks along -z
    W = int((hi[u] - lo[u]) * s) + 40; im = Image.new('RGB', (W, H), (30, 30, 34)); dr = ImageDraw.Draw(im)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
    o = np.argsort(tri[:, :, dep].mean(1) * dsg)
    for i in o:
        x = ((tri[i, :, u] * sgn - (lo[u] if sgn > 0 else -hi[u])) * s + 20); y = (H - 20 - (tri[i, :, 1] - lo[1]) * s)
        sh = 0.45 + 0.55 * abs(nrm[i, dep])
        c = tuple(int(v * sh) for v in pal[lab[i]])
        dr.polygon(list(zip(x, y)), fill=c)
    panels.append(im)
out = Image.new('RGB', (sum(p.width for p in panels) + 220, H), (30, 30, 34)); x = 0
for p in panels: out.paste(p, (x, 0)); x += p.width
dr = ImageDraw.Draw(out)
for k, p in enumerate(ids):
    dr.rectangle([x + 10, 10 + k * 22, x + 28, 28 + k * 22], fill=pal[p]); dr.text((x + 36, 12 + k * 22), f'{p}: {(lab == p).sum()}', fill=(230, 230, 230))
out.save(sys.argv[1]); print('SAVED', sys.argv[1], out.size)
