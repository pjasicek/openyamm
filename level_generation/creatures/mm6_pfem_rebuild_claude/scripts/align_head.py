"""Similarity fit of the paid v4 Meshy head (../mm6_pfem_v4_claude/meshy/head_v1, made from the same head turnaround family) onto the v3 face,
in the v3 master frame: profile match (chin .. forehead) for the start, then trimmed ICP (rotation, uniform scale, translation) of the v3 face
points onto the head surface. Writes work/head_align.json {M: 4x4 head->v3}. Args: <v3 npz> <head npz> <out json>"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import sample, profile, normals
V, H, OUT = sys.argv[1:4]
v = np.load(V); h = np.load(H)
fn = normals(v['co'], v['tri']); fc = v['co'][v['tri']].mean(1)
face = (v['part'] == 0) & (v['head'] == 1) & (fn[:, 1] < -0.25) & (fc[:, 2] > 1.375) & (fc[:, 2] < 1.52) & (np.abs(fc[:, 0]) < 0.055)
P, _ = sample(v['co'], v['tri'][face], 60000, 1)
Q, _ = sample(h['co'], h['tri'], 800000, 2)
# start: the mid profiles, chin..forehead
zv, yv = profile(sample(v['co'], v['tri'][(v['part'] == 0) & (v['head'] == 1)], 300000)[0], 1.37, 1.53, 0.004, 0.006)
zh, yh = profile(Q, -0.2, 0.95, 0.01, 0.012)
best = None
for s in np.linspace(0.16, 0.24, 41):
    for dz in np.linspace(1.33, 1.43, 101):
        yi = np.interp((zv - dz) / s, zh, yh)
        ok = ~np.isnan(yv) & ~np.isnan(yi)
        r = yv[ok] - s * yi[ok]; dy = np.median(r); e = np.mean(np.abs(r - dy))
        if best is None or e < best[0]: best = (e, s, dz, dy)
e, s, dz, dy = best
print('PROFILE', dict(err_mm=round(e * 1000, 2), s=round(s, 4), dz=round(dz, 4), dy=round(dy, 4)))
R = np.eye(3); t = np.array([0.0, dy, dz])
tree = cKDTree(Q)
for it in range(40):
    X = (P - t) @ R / s                                    # v3 face points in head space
    d, k = tree.query(X); Y = Q[k] * s @ R.T + t           # matches back in v3 space
    keep = d < np.percentile(d, 85)
    A, B = Q[k][keep], P[keep]                              # fit B ~ s R A + t
    ma, mb = A.mean(0), B.mean(0); A0, B0 = A - ma, B - mb
    U, S_, Vt = np.linalg.svd(B0.T @ A0); D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt; s = float((S_ * np.diag(D)).sum() / (A0 ** 2).sum()); t = mb - s * R @ ma
d, _ = tree.query((P - t) @ R / s)
ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
print('ICP', dict(s=round(s, 4), t=np.round(t, 4).tolist(), rot_deg=round(float(ang), 2), d_mm_p50=round(float(np.median(d) * s * 1000), 2), p90=round(float(np.percentile(d, 90) * s * 1000), 2)))
M = np.eye(4); M[:3, :3] = s * R; M[:3, 3] = t
json.dump(dict(M=M.tolist(), s=s), open(OUT, 'w'), indent=1)
