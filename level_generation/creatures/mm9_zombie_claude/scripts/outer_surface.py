"""Outer body surface for the hand tests (2026-10-30, Forad v3 Talk: the vest's standing two-layer lapel).

A face is outer when a ray from its centre along its own normal leaves the body: it hits no other body face within
`reach`. A lining (normal toward the chest) and the skin under a vest flap (normal toward the flap) are not outer;
a vest's outside, the open shirt front and bare arms are. Classified once on the bind pose, where the arms are away
from the trunk. arm_hand_gate.py and arm_clear.py use it with --outer-only: a hand point then counts as inside only
behind an outer surface, so a hand resting on a vest is not read as inside the vest's lining."""
import numpy as np
from scipy.spatial import cKDTree


def outer_faces(X, tris, faces, reach=0.06, eps=1e-4):
    """Boolean mask over `faces` (indices into tris) of the outer ones, for posed positions X."""
    T = X[tris[faces]]
    c = T.mean(1)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    size = np.linalg.norm(T - c[:, None], axis=2).max(1)
    tree = cKDTree(c)
    out = np.ones(len(faces), bool)
    for k in range(len(faces)):
        o = c[k] + n[k] * eps
        cand = np.array([j for j in tree.query_ball_point(c[k] + n[k] * reach / 2, reach / 2 + size.max())
                         if j != k], int)
        if not len(cand):
            continue
        a, b, cc = T[cand, 0], T[cand, 1], T[cand, 2]
        e1, e2 = b - a, cc - a
        p = np.cross(n[k][None], e2)
        det = np.einsum('ij,ij->i', e1, p)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = o - a
        u = np.einsum('ij,ij->i', s, p) * inv
        q = np.cross(s, e1)
        v = np.einsum('j,ij->i', n[k], q) * inv
        t = np.einsum('ij,ij->i', e2, q) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < reach)
        out[k] = not hit.any()
    return out
