"""Eyeball frames of the installed m372 LOD0 (work/lod0_before.npz): for each eye shell (pieces 10 and 11 of
work/face_piece_lod0.npy) the sphere fitted to its vertices (refitted on the inliers within 1 mm) and the forward
axis: from the centre through the middle of the part of the shell that is visible from the front between the lids
(orthographic depth test along +z against every other face of the head). The HD head views show the pupils centred in
the lid opening, looking straight ahead, so the pupil sits on that axis.
Also the opening's half-width (in metres, across x) and its angular half-height, for sizing the iris.
Usage: python3 eyefit.py (prints the frames); from code: frames() -> {piece: dict}"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
EYE_PIECES = (10, 11)


def _sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]
    sol = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    c = sol[:3]
    return c, float(np.sqrt(sol[3] + c @ c))


def frames():
    b = np.load(HERE / 'work' / 'lod0_before.npz')
    pos, tri = b['pos'], b['tri']
    piece = np.load(HERE / 'work' / 'face_piece_lod0.npy')
    out = {}
    for k in EYE_PIECES:
        verts = np.unique(tri[piece == k])
        P = pos[verts]
        c, r = _sphere(P)
        inl = np.abs(np.linalg.norm(P - c, axis=1) - r) < 0.001
        c, r = _sphere(P[inl])
        # visibility from the front: sample the shell's triangles densely, depth-test against the other faces
        ef = np.nonzero(piece == k)[0]
        rng = np.random.default_rng(k)
        n = 40000
        a3 = np.linalg.norm(np.cross(pos[tri[ef, 1]] - pos[tri[ef, 0]], pos[tri[ef, 2]] - pos[tri[ef, 0]]), axis=1)
        pick = ef[rng.choice(len(ef), n, p=a3 / a3.sum())]
        w = rng.dirichlet((1, 1, 1), n)
        pts = (pos[tri[pick]] * w[:, :, None]).sum(1)
        others = np.nonzero((piece != k) & (np.abs(pos[tri].mean(1) - c).max(1) < 0.04))[0]
        visible = np.ones(n, bool)
        for f in others:
            A, B, C = pos[tri[f]]
            # barycentric test in xy, then depth along +z (the viewer looks down -z at the face)
            v0, v1 = B[:2] - A[:2], C[:2] - A[:2]
            det = v0[0] * v1[1] - v0[1] * v1[0]
            if abs(det) < 1e-14:
                continue
            q = pts[:, :2] - A[:2]
            s = (q[:, 0] * v1[1] - q[:, 1] * v1[0]) / det
            t = (v0[0] * q[:, 1] - v0[1] * q[:, 0]) / det
            inside = (s >= 0) & (t >= 0) & (s + t <= 1)
            if not inside.any():
                continue
            z = A[2] + s * (B[2] - A[2]) + t * (C[2] - A[2])
            visible &= ~(inside & (z > pts[:, 2] + 2e-4))
        vis = pts[visible]
        mid = vis.mean(0)
        f = (mid - c) / np.linalg.norm(mid - c)
        half_w = float((np.percentile(vis[:, 0], 98) - np.percentile(vis[:, 0], 2)) / 2)
        d = (vis - c) / np.linalg.norm(vis - c, axis=1, keepdims=True)
        up = np.array([0.0, 1.0, 0.0])
        ang_up = np.degrees(np.arcsin(np.clip(d @ up - (d @ f) * (f @ up), -1, 1)))
        out[k] = {'centre': c, 'radius': r, 'forward': f, 'visible_share': float(visible.mean()),
                  'opening_half_width_m': half_w, 'opening_up_deg': float(np.percentile(ang_up, 98)),
                  'opening_down_deg': float(np.percentile(ang_up, 2))}
    return out


def eyeball_faces(fr=None, tol=0.0008):
    """Per LOD0 face: the eye piece (10 or 11) whose eyeball it lies on, else 0. The eye shells plus head-piece faces
    whose three corners lie on an eyeball's sphere (within tol) in front of its centre: the piece map (a vote of
    the nearest production faces) gave a few eyeball faces to the head."""
    fr = fr or frames()
    b = np.load(HERE / 'work' / 'lod0_before.npz')
    pos, tri = b['pos'], b['tri']
    piece = np.load(HERE / 'work' / 'face_piece_lod0.npy')
    out = np.where(np.isin(piece, EYE_PIECES), piece, 0)
    for k, f in fr.items():
        rr = np.abs(np.linalg.norm(pos[tri] - f['centre'], axis=2) - f['radius']).max(1)
        d = pos[tri].mean(1) - f['centre']
        front = (d / np.linalg.norm(d, axis=1, keepdims=True)) @ np.array([0.0, 0.0, 1.0]) > 0.3
        out[(piece == 1) & (rr < tol) & front] = k
    return out


if __name__ == '__main__':
    for k, v in frames().items():
        print(k, json.dumps({a: (np.round(b, 4).tolist() if isinstance(b, np.ndarray) else round(b, 4))
                             for a, b in v.items()}))
