"""PF4 geometry helpers (numpy only): ray casting, plane sections, section drawings."""
import numpy as np


def raycast(orig, dirs, V, T, chunk=256):
    """Nearest positive hit distance per ray (inf when none). orig (n,3) or (3,), dirs (n,3); triangles V[T]."""
    dirs = np.asarray(dirs, float); n = len(dirs)
    orig = np.broadcast_to(np.asarray(orig, float), (n, 3))
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; e1, e2 = b - a, c - a
    out = np.full(n, np.inf)
    for s in range(0, n, chunk):
        o = orig[s:s + chunk, None, :]; d = dirs[s:s + chunk, None, :]
        p = np.cross(d, e2[None]); det = (e1[None] * p).sum(-1)
        ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tv = o - a[None]; u = (tv * p).sum(-1) * inv
        q = np.cross(tv, e1[None]); v = (d * q).sum(-1) * inv; t = (e2[None] * q).sum(-1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
        out[s:s + chunk] = np.where(hit, t, np.inf).min(1)
    return out


def section(V, T, axis, value):
    """Segments where the plane coordinate[axis] == value cuts the triangles: (m, 2, 3)."""
    d = V[:, axis] - value; segs = []
    for tri in T:
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            a, b = tri[i], tri[j]
            if (d[a] > 0) != (d[b] > 0):
                t = d[a] / (d[a] - d[b]); pts.append(V[a] + t * (V[b] - V[a]))
        if len(pts) == 2: segs.append(pts)
    return np.array(segs).reshape(-1, 2, 3)


def draw_sections(path, layers, axes, centre, span, size=800, title=''):
    """layers: list of (segments, rgb); axes: two coordinate indices for image x (right) and y (up)."""
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (size, size), (250, 250, 250)); dr = ImageDraw.Draw(im)
    s = size / span
    def P(p):
        return ((p[axes[0]] - centre[0]) * s + size / 2, size / 2 - (p[axes[1]] - centre[1]) * s)
    for k in range(-10, 11):
        g = k * 0.02
        dr.line([P(np.array([centre[0] + g if i == axes[0] else (centre[1] - span) if i == axes[1] else 0 for i in range(3)])),
                 P(np.array([centre[0] + g if i == axes[0] else (centre[1] + span) if i == axes[1] else 0 for i in range(3)]))], fill=(225, 225, 225))
        dr.line([P(np.array([(centre[0] - span) if i == axes[0] else centre[1] + g if i == axes[1] else 0 for i in range(3)])),
                 P(np.array([(centre[0] + span) if i == axes[0] else centre[1] + g if i == axes[1] else 0 for i in range(3)]))], fill=(225, 225, 225))
    for segs, col in layers:
        for a, b in segs:
            dr.line([P(a), P(b)], fill=col, width=2)
    dr.text((5, 5), title + '  grid 2 cm', fill=(0, 0, 0))
    im.save(path)
