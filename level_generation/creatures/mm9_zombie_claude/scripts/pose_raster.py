#!/usr/bin/env python3
"""Fast diagnostic render of a posed GLB with the collapse gate's bad faces in red (numpy z-buffer, no Blender).
Usage: pose_raster.py <glb> <out png> <clip:time[:view]> ... ; view = azimuth deg (0 = front) [,elev]; ZOOM=<region joint>,<half size m> env."""
import sys, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
AREA = 0.2
m = Model(Glb(sys.argv[1])); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
Rs = m.skinned_positions(m.world({}))
offs = np.cumsum([0] + [len(r[0]) for r in Rs])
rest = np.concatenate([r[0] for r in Rs]); T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
J = np.concatenate([p['joints'] for p in m.primitives]); W = np.concatenate([p['weights'] for p in m.primitives])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])


def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2


n0, a0 = tri(rest)
S = int(os.environ.get('SIZE', 420))


def render(P, bad, az, el, cen, half):
    a, e = np.radians(az), np.radians(el)
    # glTF: y up, figure faces +z. camera dir from the figure
    fwd = np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
    right = np.cross([0, 1, 0], fwd); right /= np.linalg.norm(right); up = np.cross(fwd, right)
    Q = P - cen
    x = (Q @ right / half * 0.5 + 0.5) * S; y = (0.5 - Q @ up / half * 0.5) * S; z = Q @ fwd
    img = np.full((S, S, 3), 60.0); zb = np.full((S, S), -1e9)
    n, _ = tri(P); ln = np.linalg.norm(n, axis=1) + 1e-12; nn = n / ln[:, None]
    light = (right * 0.3 + up * 0.5 + fwd * 0.8); light /= np.linalg.norm(light)
    sh = 0.25 + 0.75 * np.abs(nn @ light)
    for f in np.argsort(-(bad.astype(int))):
        i, j, k = T[f]
        xs = x[[i, j, k]]; ys = y[[i, j, k]]
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, S - 1)); y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, S - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        l2 = 1 - l0 - l1
        ins = (l0 >= -0.01) & (l1 >= -0.01) & (l2 >= -0.01)
        zz = l0 * z[i] + l1 * z[j] + l2 * z[k]
        upd = ins & (zz > zb[y0:y1 + 1, x0:x1 + 1])
        zb[y0:y1 + 1, x0:x1 + 1][upd] = zz[upd]
        col = np.array([255, 40, 40.]) * (0.5 + 0.5 * sh[f]) if bad[f] else np.array([190, 185, 175.]) * sh[f]
        img[y0:y1 + 1, x0:x1 + 1][upd] = col
    return Image.fromarray(img.astype('u1'))


specs = sys.argv[3:]
cols = int(os.environ.get('COLS', 6))
sheet = Image.new('RGB', (cols * S, ((len(specs) + cols - 1) // cols) * S), (30, 30, 30))
for idx, sp in enumerate(specs):
    c, t, *v = sp.split(':')
    va = v[0].split(',') if v else ['0', '10']
    az = float(va[0]); el = float(va[1]) if len(va) > 1 else 10.0
    jn = v[1] if len(v) > 1 else None; half = float(v[2]) if len(v) > 2 else 1.1
    world = m.world(m.sample(c, float(t)))
    P = np.concatenate([r[0] for r in m.skinned_positions(world)])
    pal = world[m.joints] @ m.inverse_binds
    nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
    n, a = tri(P)
    dd = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
    bad = (a0 > 1e-9) & ((a < AREA * a0) | (dd < 0))
    if jn:
        cen = world[doc['skins'][0]['joints'][names.index('Bip01 ' + jn)]][:3, 3]
    else:
        cen = 0.5 * (P.min(0) + P.max(0))
    im = render(P, bad, az, el, cen, half)
    ImageDraw.Draw(im).text((4, 4), f'{c} {t} bad {int(bad.sum())}', fill=(255, 255, 0))
    sheet.paste(im, ((idx % cols) * S, (idx // cols) * S))
sheet.save(sys.argv[2])
