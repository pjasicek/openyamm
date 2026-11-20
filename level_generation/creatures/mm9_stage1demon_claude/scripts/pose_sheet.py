"""Posed clay sheet straight from a GLB (glb_pose skinning, PIL painter's raster): rows = clip@time, columns = front, side, 3/4.
Args: glb out.png clip@t [clip@t ...]   (t in seconds, or 'f0.5' = fraction of the clip). Env SIZE (px per view)."""
import sys, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]; specs = sys.argv[3:]
m = Model(Glb(glb)); SZ = int(os.environ.get('SIZE', 360))
durs = {}
for a in m.glb.json['animations']:
    t = 0
    for s in a['samplers']: t = max(t, float(m.glb.json['accessors'][s['input']]['max'][0]))
    durs[a['name']] = t
PR = m.primitives
def posed(clip, t):
    w = m.world(m.sample(clip, t)) if clip != 'bind' else m.world({})
    X = m.skinned_positions(w); V = []; F = []; off = 0
    for x in X:
        v = np.asarray(x[0], float); f = np.asarray(x[1]).reshape(-1, 3)
        V.append(v); F.append(f + off); off += len(v)
    return np.vstack(V), np.vstack(F)
VIEWS = [np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]), np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]]), None]
c, s_ = np.cos(np.radians(-40)), np.sin(np.radians(-40)); VIEWS[2] = np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
rows = []
for sp in specs:
    clip, tt = sp.split('@'); t = durs.get(clip, 0) * float(tt[1:]) if tt.startswith('f') else float(tt)
    V, F = posed(clip, t)                     # glTF: y up, faces +z
    row = Image.new('RGB', (SZ * 3, SZ), (40, 46, 52))
    for k, R in enumerate(VIEWS):
        Q = V @ R.T; ctr = np.array([0, 1.4, 0]); sc = SZ / 3.4
        if os.environ.get('ZOOM'):
            zx, zy, zs = [float(x) for x in os.environ['ZOOM'].split(',')]; ctr = np.array([zx, zy, 0]) @ R.T * np.array([1, 1, 0]) + np.array([0, zy, 0]) * 0; ctr[1] = zy; sc = SZ / zs
        im = Image.new('RGB', (SZ, SZ), (40, 46, 52)); d = ImageDraw.Draw(im)
        tri = Q[F]; nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        order = np.argsort(tri[:, :, 2].mean(1))
        L = np.array([0.3, 0.5, 0.8]); L /= np.linalg.norm(L)
        for i in order:
            sh = int(50 + 170 * abs(nrm[i] @ L)); X = (tri[i, :, 0] - ctr[0]) * sc + SZ / 2; Y = SZ / 2 - (tri[i, :, 1] - ctr[1]) * sc
            d.polygon(list(zip(X, Y)), fill=(sh, sh, sh))
        d.line([(0, SZ / 2 + ctr[1] * sc), (SZ, SZ / 2 + ctr[1] * sc)], fill=(90, 160, 90))
        if k == 0: d.text((4, 4), f'{clip} {t:.2f}s', fill=(255, 255, 120))
        row.paste(im, (k * SZ, 0))
    rows.append(row)
sheet = Image.new('RGB', (SZ * 3 * ((len(rows) + 1) // 2), SZ * 2 if len(rows) > 1 else SZ), (0, 0, 0))
for i, r in enumerate(rows): sheet.paste(r, ((i // 2) * SZ * 3, (i % 2) * SZ))
sheet.save(out); print('SHEET', out, len(rows))
