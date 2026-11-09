#!/usr/bin/env python3
"""Two-way posed surface error of a reduced GLB against the installed one, the way reduce_ladder.py measures it (every 3rd frame
at 24 fps of every clip, vertex -> nearest surface both ways, all primitives), in Python: the candidate's vertices are installed
vertices (distance 0), so the error is the installed vertices' distance to the candidate surface (exact point-triangle distance
over the 200 nearest candidate triangles by centroid; 24 missed large faces). Prints p99 and max (mm) and the worst clip:frame, plus the limits
3/15 mm per metre of height. Usage: surface_error.py <installed.glb> <candidate.glb> <height_m>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402


def pt_tri(p, a, b, c):
    """distance from points p (n,3) to triangles (n,k,3) a,b,c broadcast: Ericson's closest point, vectorised"""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b; d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c; d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den; q = a + ab * v[..., None] + ac * w[..., None]
    eps = 1e-30
    t = np.clip(d1 / np.where(np.abs(d1 - d3) < eps, eps, d1 - d3), 0, 1)
    qab = a + ab * t[..., None]
    t2 = np.clip(d2 / np.where(np.abs(d2 - d6) < eps, eps, d2 - d6), 0, 1)
    qac = a + ac * t2[..., None]
    bc = c - b; t3 = np.clip(((p - b) * bc).sum(-1) / np.maximum((bc * bc).sum(-1), eps), 0, 1)
    qbc = b + bc * t3[..., None]
    inside = (va >= 0) & (vb >= 0) & (vc >= 0)
    dist = np.where(inside, np.linalg.norm(p - q, axis=-1), np.inf)
    for qq in (qab, qac, qbc):
        dist = np.minimum(dist, np.linalg.norm(p - qq, axis=-1))
    return dist


A, B, H = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2])), float(sys.argv[3])
allerr = []; worst = (0, '')
for clip in [a['name'] for a in A.glb.json['animations']]:
    t1 = A.clip_times(clip)[-1]
    for f, t in enumerate(np.arange(0, t1 + 1e-6, 3 / 24)):
        pa = A.skinned_positions(A.world(A.sample(clip, t))); pb = B.skinned_positions(B.world(B.sample(clip, t)))
        Pa = np.concatenate([p for p, _ in pa]); Pb = np.concatenate([p for p, _ in pb])
        off = np.cumsum([0] + [len(p) for p, _ in pb])
        Tb = np.concatenate([np.asarray(tr).reshape(-1, 3) + off[k] for k, (_, tr) in enumerate(pb)])
        cen = Pb[Tb].mean(1); _, nn = cKDTree(cen).query(Pa, k=200)
        tri = Pb[Tb[nn]]
        d = pt_tri(Pa[:, None, :], tri[:, :, 0], tri[:, :, 1], tri[:, :, 2]).min(1)
        d = np.concatenate([d, np.zeros(len(Pb))])   # candidate -> installed: every candidate vertex is an installed vertex
        allerr.append(d)
        if d.max() > worst[0]:
            worst = (d.max(), f'{clip}:{f * 3}')
e = np.concatenate(allerr)
p99, mx = np.percentile(e, 99) * 1000, worst[0] * 1000
print(f'{Path(sys.argv[2]).name}: p99 {p99:.2f} mm, max {mx:.2f} mm at {worst[1]}; limits for {H} m: p99 {3 * H:.2f}, max {15 * H:.2f} '
      f'-> {"PASS" if p99 <= 3 * H and mx <= 15 * H else "fail"}')
