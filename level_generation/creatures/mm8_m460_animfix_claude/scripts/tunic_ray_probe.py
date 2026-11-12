#!/usr/bin/env python3
"""Legs seen through a skinned tunic skirt from the front (the MM6 Cleric: front panel weighted to both thighs, so a
far-swung thigh's trousers can come out in front of it). A grid of rays along -Z (2 cm spacing over the skirt band);
a ray counts when its first hit is a leg vertex (rest depth: within LEG m of its thigh bone axis in Standing) while
in Standing the same ray first hits skirt cloth (farther than LEG + 2 cm). Per clip (30 Hz): share of samples with
such a ray, the most such rays at once (each ~4 cm2) and the mean.

    tunic_ray_probe.py <glb> <clip>[,<clip>...] [--band 0.45,0.85] [--leg 0.085]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
band = [float(x) for x in opts.get('band', '0.45,0.85').split(',')]
LEG = float(opts.get('leg', 0.085))
g = open_glb(args[0])
M = glb_pose.Model(g)
names = [n['name'] for n in g.json['nodes']]
I = {n: i for i, n in enumerate(names)}
p = M.primitives[0]
tri = p['triangles']
W0 = M.world(M.sample('Standing', 0.0))
P0, _ = M.skinned_positions(W0)[0]


def seg(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + np.outer(t, ab)), axis=1)


axis_d = np.min([seg(P0, W0[I[f'B_{s}_Thigh'], :3, 3], W0[I[f'B_{s}_Calf'], :3, 3]) for s in 'LR'], axis=0)
dom = np.array([names[M.joints[j]] for j in p['joints'][np.arange(len(P0)), p['weights'].argmax(1)]])
cloth = np.array([d.startswith(('Cloak', 'Robe')) for d in dom])
xs = np.arange(-0.2, 0.2001, 0.02)
ys = np.arange(band[0], band[1] + 1e-6, 0.02)


def first_hits(P):
    v0 = P[tri[:, 0]]
    e1 = P[tri[:, 1]] - v0
    e2 = P[tri[:, 2]] - v0
    d = np.array([0, 0, -1.0])
    pv = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, pv)
    good = np.abs(det) > 1e-12
    out = {}
    for x in xs:
        for y in ys:
            o = np.array([x, y, 2.0])
            # cull triangles whose box misses the ray
            lo = np.minimum(np.minimum(P[tri[:, 0]], P[tri[:, 1]]), P[tri[:, 2]])
            hi = np.maximum(np.maximum(P[tri[:, 0]], P[tri[:, 1]]), P[tri[:, 2]])
            c = good & (lo[:, 0] <= x) & (hi[:, 0] >= x) & (lo[:, 1] <= y) & (hi[:, 1] >= y)
            if not c.any():
                continue
            idx = np.where(c)[0]
            tv = o - v0[idx]
            u = np.einsum('ij,ij->i', tv, pv[idx]) / det[idx]
            q = np.cross(tv, e1[idx])
            v = (q @ d) / det[idx]
            t = np.einsum('ij,ij->i', e2[idx], q) / det[idx]
            ok = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
            if ok.any():
                k = idx[ok][np.argmin(t[ok])]
                out[(round(x, 3), round(y, 3))] = tri[k]
    return out


def kind(vs):
    if cloth[vs].any():
        return 'cloth'
    d = axis_d[vs].mean()
    return 'leg' if d < LEG else ('skirt' if d > LEG + 0.02 else 'mid')


rest = {k: kind(v) for k, v in first_hits(P0).items()}
skirt_rays = {k for k, v in rest.items() if v == 'skirt'}
print(f'skirt rays in Standing: {len(skirt_rays)}')
for clip in args[1].split(','):
    T = M.clip_times(clip)[-1]
    counts = []
    for t in np.arange(0, T, 1 / 30):
        P, _ = M.skinned_positions(M.world(M.sample(clip, float(t))))[0]
        hits = first_hits(P)
        counts.append(sum(1 for k in skirt_rays if k in hits and kind(hits[k]) == 'leg'))
    c = np.array(counts)
    print(f'{clip:9s} legs through the skirt: {100 * (c > 0).mean():.0f}% of samples, most {c.max()} rays, '
          f'mean {c.mean():.1f}')
