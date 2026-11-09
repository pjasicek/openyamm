"""closest_on_tris from mm9_ebora_reduce_claude/scripts/interp_weights.py (Ericson)."""
import numpy as np


def closest_on_tris(p, a, b, c):
    """Ericson's closest point on triangle, vectorised; returns barycentric (u, v, w) for a, b, c"""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b; d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c; d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den; bary = np.stack([1 - v - w, v, w], -1)
    def setb(m, x):
        bary[m] = x[m]
    ones = lambda *k: np.stack(k, -1)
    z = np.zeros_like(d1); o = np.ones_like(d1)
    # edge and vertex regions (order matters: later rules win only where their conditions hold)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3); setb(m, ones(1 - t, t, z))
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6); setb(m, ones(1 - t, z, t))
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6)); setb(m, ones(z, 1 - t, t))
    setb((d1 <= 0) & (d2 <= 0), ones(o, z, z)); setb((d3 >= 0) & (d4 <= d3), ones(z, o, z)); setb((d6 >= 0) & (d5 <= d6), ones(z, z, o))
    q = bary[..., :1] * a + bary[..., 1:2] * b + bary[..., 2:] * c
    return bary, np.linalg.norm(p - q, axis=-1)


