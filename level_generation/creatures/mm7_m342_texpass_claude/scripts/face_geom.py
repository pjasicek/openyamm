"""Face geometry of the m342 LOD0 (bind pose, glTF metres, +z forward): eyeball spheres, their visible lid openings and
forward axes, and a front depth buffer of the face skin. Used by face_paint.py and uv_eyes.py.

- eyes(): per eyeball piece (22 right, 30 left) a least-squares sphere; the eyeball points in front of the skin shell
  seen along +z (the eyeballs sit behind a closed skin shell with an opening where the lids part) form the opening; the
  forward axis is the direction from the centre to the opening's area-weighted centroid (the HD front view: irises
  centred in the opening, looking ahead).
- front_depth(): largest z of chosen faces per (x, y), orthographic along +z."""
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
EYES = {22: 'right', 30: 'left'}
SHELL = 1


def sphere(v):
    A = np.c_[2 * v, np.ones(len(v))]
    sol = np.linalg.lstsq(A, (v ** 2).sum(1), rcond=None)[0]
    c = sol[:3]
    return c, float(np.sqrt(sol[3] + c @ c))


def front_depth(xyz, faces, points, step=0.0002):
    lo = points[:, :2].min(0) - 0.003
    hi = points[:, :2].max(0) + 0.003
    n = np.ceil((hi - lo) / step).astype(int) + 1
    zbuf = np.full((n[1], n[0]), -np.inf)
    for t in faces:
        q = (xyz[t][:, :2] - lo) / step
        x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int) + 1, n)
        if x1 <= x0 or y1 <= y0:
            continue
        M = np.array([q[1] - q[0], q[2] - q[0]]).T
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        st = np.linalg.solve(M, np.stack([gx.ravel() - q[0, 0], gy.ravel() - q[0, 1]]))
        b = np.stack([1 - st[0] - st[1], st[0], st[1]], 1)
        ok = (b >= -1e-6).all(1)
        np.maximum.at(zbuf, (gy.ravel()[ok], gx.ravel()[ok]), b[ok] @ xyz[t][:, 2])
    q = np.round((points[:, :2] - lo) / step).astype(int)
    return zbuf[np.clip(q[:, 1], 0, n[1] - 1), np.clip(q[:, 0], 0, n[0] - 1)]


def eyes(samples=60000, seed=0):
    d = np.load(HERE / 'work' / 'lod0_before.npz')
    pos, tri, piece = d['pos'], d['tri'], d['piece']
    xyz = pos[tri]
    rng = np.random.default_rng(seed)
    out = {}
    for k in EYES:
        f = np.nonzero(piece == k)[0]
        c, R = sphere(np.unique(xyz[f].reshape(-1, 3), axis=0))
        near = np.nonzero((piece == SHELL) & (np.linalg.norm(xyz.mean(1) - c, axis=1) < 0.035))[0]
        a = np.linalg.norm(np.cross(xyz[f, 1] - xyz[f, 0], xyz[f, 2] - xyz[f, 0]), axis=1)
        t = rng.choice(f, samples, p=a / a.sum())
        b = rng.dirichlet((1, 1, 1), samples)
        p = (xyz[t] * b[:, :, None]).sum(1)
        vis = p[:, 2] > front_depth(xyz, near, p)
        dirs = p[vis] - c
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        axis = dirs.mean(0)
        axis /= np.linalg.norm(axis)
        ang = np.degrees(np.arccos(np.clip(dirs @ axis, -1, 1)))
        out[k] = {'centre': c, 'radius': R, 'axis': axis, 'visible_share': float(vis.mean()),
                  'opening_p95_deg': float(np.percentile(ang, 95)), 'opening_points': p[vis]}
    return out


if __name__ == '__main__':
    for k, e in eyes().items():
        x, y = e['opening_points'][:, 0], e['opening_points'][:, 1]
        print(EYES[k], 'centre', e['centre'].round(4), 'R %.4f' % e['radius'], 'axis', e['axis'].round(3),
              'to +z %.1f deg' % np.degrees(np.arccos(e['axis'][2])), 'visible %.0f%%' % (100 * e['visible_share']),
              'opening p95 %.0f deg' % e['opening_p95_deg'], 'opening w x h mm %.1f x %.1f' % (np.ptp(x) * 1e3, np.ptp(y) * 1e3))
