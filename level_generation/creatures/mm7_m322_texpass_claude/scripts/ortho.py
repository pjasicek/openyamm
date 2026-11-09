"""Orthographic close-up of the bind-pose LOD0 with any texture on the texture-pass layout (or the installed one):
z-buffered per-pixel UV, nearest triangle wins, flat lighting off (pure albedo) unless shade > 0.
Usage (module): render(image (H,W,3) float, layout uv (T,3,2), xyz (T,3,3), view, centre (x,y), half-size m, px)."""
import numpy as np

VIEWS = {'front': (np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])),
         'back': (np.array([-1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, -1])),
         'left': (np.array([0, 0, -1]), np.array([0, 1, 0]), np.array([1, 0, 0])),
         'right': (np.array([0, 0, 1]), np.array([0, 1, 0]), np.array([-1, 0, 0])),
         'quarter': (np.array([0.7071, 0, -0.7071]), np.array([0, 1, 0]), np.array([0.7071, 0, 0.7071]))}


def render(img, uv, xyz, view='front', centre=(0.0, 1.6), half=0.15, px=600, shade=0.0, faces=None):
    ax, ay, az = VIEWS[view]
    h, w = img.shape[:2]
    P = np.stack([xyz @ ax, xyz @ ay, xyz @ az], -1)            # (T,3,3)
    sx = (P[..., 0] - (centre[0] if view in ('front', 'back') else 0) + half) / (2 * half) * px
    if view not in ('front', 'back'):
        sx = (P[..., 0] - centre[0] + half) / (2 * half) * px
    sy = (centre[1] + half - P[..., 1]) / (2 * half) * px
    depth = P[..., 2]
    zbuf = np.full((px, px), -np.inf)
    out = np.zeros((px, px, 3))
    nrm = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    lit = np.clip(np.abs(nrm @ az), 0, 1)
    idx = range(len(uv)) if faces is None else np.nonzero(faces)[0]
    for t in idx:
        x, y, z = sx[t], sy[t], depth[t]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()) + 1, px))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()) + 1, px))
        if x1 <= x0 or y1 <= y0:
            continue
        M = np.array([[x[1] - x[0], x[2] - x[0]], [y[1] - y[0], y[2] - y[0]]])
        det = np.linalg.det(M)
        if abs(det) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        st = np.linalg.solve(M, np.stack([gx.ravel() - x[0], gy.ravel() - y[0]]))
        b = np.stack([1 - st[0] - st[1], st[0], st[1]], 1)
        ok = (b >= -1e-4).all(1)
        if not ok.any():
            continue
        b = b[ok]
        zz = b @ z
        yy, xx = (gy.ravel()[ok] - 0.5).astype(int), (gx.ravel()[ok] - 0.5).astype(int)
        front = zz > zbuf[yy, xx]
        if not front.any():
            continue
        b, yy, xx, zz = b[front], yy[front], xx[front], zz[front]
        u = b @ uv[t]
        cx = np.clip(u[:, 0] * w - 0.5, 0, w - 1.001)
        cy = np.clip(u[:, 1] * h - 0.5, 0, h - 1.001)
        ix, iy = cx.astype(int), cy.astype(int)
        fx, fy = (cx - ix)[:, None], (cy - iy)[:, None]
        col = (img[iy, ix] * (1 - fx) * (1 - fy) + img[iy, ix + 1] * fx * (1 - fy)
               + img[iy + 1, ix] * (1 - fx) * fy + img[iy + 1, ix + 1] * fx * fy)
        if shade:
            col = col * (1 - shade + shade * lit[t])
        out[yy, xx] = col
        zbuf[yy, xx] = zz
    return out
