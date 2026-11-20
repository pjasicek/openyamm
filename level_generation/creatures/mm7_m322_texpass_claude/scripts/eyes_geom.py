"""Eye geometry of the m322 LOD0 (bind pose): per eyeball shell (pieces 4 and 5) a sphere fit, the part of the shell
in front of the face skin (the eyeballs pass through the closed skin shell; there is no lid hole) seen along +z, the
visible area's centre direction, and the installed pupil (darkest texels inside the visible area).
geometry(xyz, piece) -> {piece: {'centre', 'radius', 'visible_dir'}}; skin_depth(...) -> front skin z per point."""
import numpy as np


def sphere(v):
    A = np.c_[2 * v, np.ones(len(v))]
    sol = np.linalg.lstsq(A, (v ** 2).sum(1), rcond=None)[0]
    c = sol[:3]
    return c, float(np.sqrt(sol[3] + c @ c))


def skin_depth(xyz, faces, points, step=0.0001):
    """Largest z of the given faces at each point's (x, y), -inf where none covers it (orthographic along +z)."""
    lo = points[:, :2].min(0) - 0.002
    hi = points[:, :2].max(0) + 0.002
    n = np.ceil((hi - lo) / step).astype(int) + 1
    zbuf = np.full((n[1], n[0]), -np.inf)
    for t in np.nonzero(faces)[0]:
        p = xyz[t]
        q = (p[:, :2] - lo) / step
        x0, y0 = np.floor(q.min(0)).astype(int)
        x1, y1 = np.ceil(q.max(0)).astype(int) + 1
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, n[0]), min(y1, n[1])
        if x1 <= x0 or y1 <= y0:
            continue
        M = np.array([q[1] - q[0], q[2] - q[0]]).T
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        st = np.linalg.solve(M, np.stack([gx.ravel() - q[0, 0], gy.ravel() - q[0, 1]]))
        b = np.stack([1 - st[0] - st[1], st[0], st[1]], 1)
        ok = (b >= -1e-6).all(1)
        z = b[ok] @ p[:, 2]
        yy, xx = gy.ravel()[ok], gx.ravel()[ok]
        np.maximum.at(zbuf, (yy, xx), z)
    q = np.round((points[:, :2] - lo) / step).astype(int)
    return zbuf[np.clip(q[:, 1], 0, n[1] - 1), np.clip(q[:, 0], 0, n[0] - 1)]


def geometry(xyz, piece, skin_faces, samples=40000, seed=0):
    out = {}
    rng = np.random.default_rng(seed)
    for k in (4, 5):
        f = np.nonzero(piece == k)[0]
        c, R = sphere(np.unique(xyz[f].reshape(-1, 3), axis=0))
        t = rng.choice(f, samples)
        b = rng.dirichlet((1, 1, 1), samples)
        pt = (xyz[t] * b[:, :, None]).sum(1)
        near = np.linalg.norm(xyz[skin_faces].mean(1) - c, axis=1) < 0.03
        sz = skin_depth(xyz, np.where(skin_faces)[0][near] if False else (skin_faces & np.isin(np.arange(len(xyz)),
                        np.nonzero(skin_faces)[0][near])), pt)
        vis = pt[:, 2] > sz
        d = pt[vis] - c
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        vdir = d.mean(0)
        vdir /= np.linalg.norm(vdir)
        out[k] = {'centre': c, 'radius': R, 'visible_dir': vdir, 'visible_share': float(vis.mean()),
                  'samples': (t, b, pt, vis)}
    return out
