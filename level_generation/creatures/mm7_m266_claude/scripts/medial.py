#!/usr/bin/env python3
"""Joint refinement on the medial axis (numpy, outside Blender; input from dump_mesh.py).
For every joint of every chain in a draft joints json: candidates on the plane normal to the chain at that joint
(within SEARCH m), kept when inside the closed skin (odd +Z ray crossings over the skin triangles), scored by the
distance to the nearest skin vertex; the joint moves to the best one (a joint whose clearance cannot grow stays).
Prints clearance before/after. Args: <npz> <draft json> <out json> [piece ids also counted as skin, comma list]"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
a = sys.argv[1:]
d = np.load(a[0]); co, tri, pv = d['co'], d['tri'], d['piece'].copy()
extra = [int(x) for x in a[3].split(',')] if len(a) > 3 and a[3] else []
for p in extra:
    pv[pv == p] = 0
skin_t = tri[pv[tri].min(1) == 0]
V = co[skin_t]
kd = cKDTree(co[pv == 0])
SEARCH = 0.09


def inside(p):
    # +Z ray: count triangles whose xy projection contains p and lie above it
    A, B, C = V[:, 0], V[:, 1], V[:, 2]
    def cross2(u, v):
        return u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    pa, pb, pc = A[:, :2] - p[:2], B[:, :2] - p[:2], C[:, :2] - p[:2]
    s1, s2, s3 = cross2(pa, pb), cross2(pb, pc), cross2(pc, pa)
    hit = ((s1 > 0) & (s2 > 0) & (s3 > 0)) | ((s1 < 0) & (s2 < 0) & (s3 < 0))
    if not hit.any():
        return False
    tot = s1 + s2 + s3
    z = (s2[hit] * A[hit, 2] + s3[hit] * B[hit, 2] + s1[hit] * C[hit, 2]) / tot[hit]
    return int((z > p[2]).sum()) % 2 == 1


def refine(chain, fixed=()):
    J = np.array(chain, float); out = J.copy(); rep = []
    for i in range(len(J)):
        before = kd.query(J[i])[0]
        if i in fixed:
            rep.append((round(before, 3), round(before, 3), inside(J[i]))); continue
        t = J[min(i + 1, len(J) - 1)] - J[max(i - 1, 0)]; t /= np.linalg.norm(t)
        u = np.cross(t, [0, 0, 1.0]) if abs(t[2]) < 0.9 else np.cross(t, [1.0, 0, 0]); u /= np.linalg.norm(u)
        w = np.cross(t, u)
        best = (before if inside(J[i]) else -1.0, J[i])
        for r in np.linspace(0.015, SEARCH, 6):
            for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                q = J[i] + r * (np.cos(ang) * u + np.sin(ang) * w)
                dq = kd.query(q)[0]
                if dq > best[0] + 0.004 and inside(q):
                    best = (dq, q)
        out[i] = best[1]
        rep.append((round(before, 3), round(float(best[0]), 3), inside(out[i])))
    return out, rep


if __name__ == '__main__':
    D = json.load(open(a[1]))
    res = {'chains': {}}
    for name, ch in D['chains'].items():
        fixed = set(D.get('fixed', {}).get(name, []))
        J, rep = refine(ch, fixed)
        res['chains'][name] = J.round(4).tolist()
        print(name, rep)
    for k in D:
        if k not in ('chains',):
            res[k] = D[k]
    json.dump(res, open(a[2], 'w'), indent=1)
