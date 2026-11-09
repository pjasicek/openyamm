#!/usr/bin/env python3
"""Translation-only kilt controls re-solved for a new clip (package h20, the MM8 Minotaur's mail kilt).

The Minotaur (`mm8_m484`) kilt hangs from twelve `Skirt_*` bones (children of the pelvis and thighs) that only
translate: its project fitted them per frame so the kilt's triangles clear the closed body underneath
(`../../mm8_m484_claude/scripts/solve_cloth.py`: least squares of the control offsets against contact pushes, belt kept
by the skin, regularised 0.025, step 0.75, each control capped at 0.30 m, warm start from the previous frame x 0.94).
A new clip that copies the base clip's (phase-aligned) control offsets leaves them fitted to the base clip's legs, so a
higher knee drive goes through the kilt front. This is a numpy version of that solver on the composed pose:

- kilt points: LOD0 vertices with any `Skirt_` weight whose bind height is below `top` (the project's 0.89 m: the
  waist band is left to the skin), plus the centroids and edge midpoints of the triangles between them; body: the
  triangles whose vertices have no `Skirt_` weight and are dominated by the pelvis, spine or leg bones;
- a kilt point is in contact when it is less than `gap` (default 0: inside) in front of the nearest point on the body's
  triangles along that triangle's normal (the project tested triangle overlaps); its target is that point + normal x
  `margin` (1 cm);
- offsets D (world, per control) solve (A^T A + 0.025 I) delta = A^T d, D += 0.75 delta, capped at 0.30 m, up to
  `iterations` passes per sample; two passes round the loop so the warm start is periodic; then a periodic Gaussian
  blur of `sigma` samples and a final contact pass without warm-start decay.

`from_base`: start from the base clip's phase-aligned offsets and cap only the correction added to them (the
accepted look is kept where the new legs do not reach the kilt).

Each control's local translation = its rest translation + R_parent^-1 D (the controls have no children).
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

import gaitlib
from gaitlib import glb_pose

BODY_BONES = ('B_Pelvis', 'B_Spine', 'Thigh', 'Calf', 'Foot')


def setup(P, cfg):
    prefix = cfg.get('prefix', 'Skirt_')
    names = [n['name'] for n in P.nodes]
    prim = P.model.primitives[0]
    joints = np.asarray(P.model.joints)
    W = prim['weights']
    J = prim['joints']
    controls = [j for j in range(len(joints)) if names[joints[j]].startswith(prefix)]
    A_full = np.zeros((len(W), len(controls)))
    for c, j in enumerate(controls):
        A_full[:, c] = (W * (J == j)).sum(axis=1)
    skirt_w = A_full.sum(axis=1)
    dom = np.array([names[joints[j]] for j in J[np.arange(len(J)), W.argmax(axis=1)]])
    rest = prim['positions']
    top = float(cfg.get('top', 0.89))
    kilt = np.where((skirt_w > 0.0) & (rest[:, 1] < top))[0]
    body_v = (skirt_w == 0.0) & np.array([any(b in d for b in BODY_BONES) for d in dom])
    tris = prim['triangles']
    body = tris[body_v[tris].all(axis=1)]
    # samples: kilt vertices, the centroids of kilt triangles and their edge midpoints (big reduced-mesh triangles)
    in_kilt = np.zeros(len(rest), bool)
    in_kilt[kilt] = True
    kt = tris[in_kilt[tris].all(axis=1)]
    edges = np.unique(np.sort(np.concatenate([kt[:, [0, 1]], kt[:, [1, 2]], kt[:, [2, 0]]]), axis=1), axis=0)
    idx = np.concatenate([np.stack([kilt] * 3, axis=1), kt, np.concatenate([edges, edges[:, :1]], axis=1)])
    w = np.concatenate([np.tile([1.0, 0.0, 0.0], (len(kilt), 1)), np.full((len(kt), 3), 1.0 / 3),
                        np.tile([0.5, 0.5, 0.0], (len(edges), 1))])
    A = np.einsum('sk,skc->sc', w, A_full[idx])
    return {'controls': [int(joints[j]) for j in controls], 'A': A, 'kilt': kilt, 'sample_idx': idx,
            'sample_w': w, 'body': body, 'triangles': tris}


def samples(S, pts):
    return np.einsum('sk,skc->sc', S['sample_w'], pts[S['sample_idx']])


def pose_points(P, W_pose):
    """Posed LOD0 vertices (first primitive) for one world-matrix set."""
    return P.model.skinned_positions(W_pose)[0][0]


def closest_on_triangles(p, a, b, c):
    """Closest points on triangles (a, b, c) to points p, all (n, 3) (Ericson, Real-Time Collision Detection 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = np.einsum('ij,ij->i', ab, ap), np.einsum('ij,ij->i', ac, ap)
    bp = p - b
    d3, d4 = np.einsum('ij,ij->i', ab, bp), np.einsum('ij,ij->i', ac, bp)
    cp = p - c
    d5, d6 = np.einsum('ij,ij->i', ab, cp), np.einsum('ij,ij->i', ac, cp)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    denom = np.maximum(va + vb + vc, 1e-18)
    v, w = vb / denom, vc / denom
    out = a + ab * v[:, None] + ac * w[:, None]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = d1 / np.where(np.abs(d1 - d3) > 1e-18, d1 - d3, 1e-18)
    out[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = d2 / np.where(np.abs(d2 - d6) > 1e-18, d2 - d6, 1e-18)
    out[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where(np.abs((d4 - d3) + (d5 - d6)) > 1e-18, (d4 - d3) + (d5 - d6), 1e-18)
    out[m] = (b + (c - b) * t[:, None])[m]
    out[(d1 <= 0) & (d2 <= 0)] = a[(d1 <= 0) & (d2 <= 0)]
    out[(d3 >= 0) & (d4 <= d3)] = b[(d3 >= 0) & (d4 <= d3)]
    out[(d6 >= 0) & (d5 <= d6)] = c[(d6 >= 0) & (d5 <= d6)]
    return out


class Surface:
    """Posed body triangles: nearest point and its face normal for query points (k nearest centroids searched)."""

    def __init__(self, points, triangles):
        self.a, self.b, self.c = (points[triangles[:, i]] for i in range(3))
        n = np.cross(self.b - self.a, self.c - self.a)
        self.n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        self.tree = cKDTree((self.a + self.b + self.c) / 3)

    def nearest(self, p, k=12):
        _, idx = self.tree.query(p, k=k)
        best_d = np.full(len(p), np.inf)
        best_q = np.zeros_like(p)
        best_n = np.zeros_like(p)
        for j in range(k):
            t = idx[:, j]
            q = closest_on_triangles(p, self.a[t], self.b[t], self.c[t])
            d = np.linalg.norm(p - q, axis=1)
            better = d < best_d - 1e-9
            best_d[better], best_q[better], best_n[better] = d[better], q[better], self.n[t][better]
        return best_d, best_q, best_n


def solve_sample(base_kilt, A, surface, D, cfg, D0=None):
    gap, margin = float(cfg.get('gap', 0.0)), float(cfg.get('margin', 0.010))
    reg, step, cap = float(cfg.get('reg', 0.025)), float(cfg.get('step', 0.75)), float(cfg.get('cap', 0.30))
    contacts = 0
    for it in range(int(cfg.get('iterations', 80))):
        pts = base_kilt + A @ D
        dist, q, nrm = surface.nearest(pts)
        depth = np.einsum('ij,ij->i', pts - q, nrm)
        hit = np.where((dist < 0.15) & (depth < gap) & (np.linalg.norm(A, axis=1) > 0.02))[0]
        if it == 0:
            contacts = len(hit)
        if not len(hit):
            break
        a = A[hit]
        d = q[hit] + nrm[hit] * margin - pts[hit]
        delta = np.linalg.solve(a.T @ a + np.eye(A.shape[1]) * reg, a.T @ d)
        D = D + delta * step
        ref = np.zeros_like(D) if D0 is None else D0
        lengths = np.linalg.norm(D - ref, axis=1)
        D = ref + (D - ref) * np.minimum(1.0, cap / np.maximum(lengths, 1e-8))[:, None]
    return D, contacts


def solve_kilt(P, worlds, base_local, cfg, report):
    """Re-solve the kilt controls of a composed clip; returns base_local with the controls' translations replaced."""
    S = setup(P, cfg)
    ctrl = S['controls']
    N = len(worlds)
    base_kilt, surfaces, parent_rot = [], [], []
    for i in range(N):
        W = worlds[i].copy()
        for node in ctrl:
            t, r, s = P.model.rest[node]
            local = base_local[i].get(node, P.model.rest[node])
            W[node] = W[P.parent[node]] @ glb_pose.trs_matrix(t, local[1], local[2])
        pts = pose_points(P, W)
        base_kilt.append(samples(S, pts))
        surfaces.append(Surface(pts, S['body']))
        parent_rot.append([W[P.parent[node]][:3, :3] for node in ctrl])
    D0 = np.zeros((N, len(ctrl), 3))
    if cfg.get('from_base'):
        # keep the base clip's (phase-aligned) offsets and add only the correction the new legs need
        for i in range(N):
            for c, node in enumerate(ctrl):
                local = base_local[i].get(node, P.model.rest[node])
                D0[i, c] = parent_rot[i][c] @ (np.asarray(local[0]) - P.model.rest[node][0])
    first = [solve_sample(base_kilt[i], S['A'], surfaces[i], D0[i], dict(cfg, iterations=1))[1] for i in range(N)]
    if cfg.get('from_base'):
        sol = np.array([solve_sample(base_kilt[i], S['A'], surfaces[i], D0[i], cfg, D0[i])[0] for i in range(N)])
    else:
        D = np.zeros((len(ctrl), 3))
        sol = [None] * N
        for loop in range(2):
            for i in range(N):
                D, _ = solve_sample(base_kilt[i], S['A'], surfaces[i], D * 0.94, cfg)
                sol[i] = D
        sol = np.array(sol)
    sigma = float(cfg.get('sigma', 1.0))
    if sigma > 0:
        sol = D0 + gaussian_filter1d(sol - D0, sigma, axis=0, mode='wrap')
    left, moved = [], []
    for i in range(N):
        D, _ = solve_sample(base_kilt[i], S['A'], surfaces[i], sol[i], cfg, D0[i] if cfg.get('from_base') else None)
        sol[i] = D
        _, after = solve_sample(base_kilt[i], S['A'], surfaces[i], D, dict(cfg, iterations=1))
        left.append(after)
        moved.append(float(np.linalg.norm(D - D0[i], axis=1).max()))
    out = []
    for i in range(N):
        local = dict(base_local[i])
        for c, node in enumerate(ctrl):
            t, r, s = P.model.rest[node]
            old = local.get(node, P.model.rest[node])
            local[node] = [t + parent_rot[i][c].T @ sol[i][c], old[1], old[2]]
        out.append(local)
    report['kilt_solve'] = {'controls': len(ctrl), 'kilt_points': int(len(S['kilt'])), 'samples': int(len(S['A'])),
                            'contacts_before_max': int(max(first)), 'contacts_after_max': int(max(left)),
                            'max_correction_m': float(max(moved)), 'from_base': bool(cfg.get('from_base'))}
    return out
