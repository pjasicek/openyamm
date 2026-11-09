"""Curve deform of the Meshy tail onto the MM9 tail chain (fit_mm9.py, Imp)."""
import numpy as np


def catmull(P, n=200):
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        for t in np.linspace(0, 1, n // (len(P) - 3), endpoint=False):
            a, b, c, d = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3))
    out.append(P[-2])
    return np.array(out)


def arclen(C):
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]


def frames(C):
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = np.zeros_like(T)
    u = np.array([1.0, 0, 0])
    n = u - T[0] * (u @ T[0]); N[0] = n / np.linalg.norm(n)
    for i in range(1, len(C)):
        n = N[i - 1] - T[i] * (N[i - 1] @ T[i]); N[i] = n / np.linalg.norm(n)
    return T, N, np.cross(T, N)


def tail_curve(X, mask, chain, tip, cfg):
    """Centreline of the masked tail by bands along its own path (y grows along it), mapped by arc-length fraction onto
    chain + tip. Root: the first `blend` of the tail blends the move out, so it stays joined to the body."""
    ids = np.nonzero(mask)[0]
    Q = X[ids]
    ys = np.linspace(Q[:, 1].min(), Q[:, 1].max(), cfg.get('bands', 40))
    cents = []
    for a, b in zip(ys[:-1], ys[1:]):
        m = (Q[:, 1] >= a) & (Q[:, 1] <= b)
        if m.sum() >= 3:
            cents.append(0.5 * (Q[m].min(0) + Q[m].max(0)))
    cents = np.array(cents)
    # smooth the centreline
    for _ in range(3):
        cents[1:-1] = 0.25 * cents[:-2] + 0.5 * cents[1:-1] + 0.25 * cents[2:]
    src = catmull(cents, 400)
    dst = catmull(np.vstack([chain, tip]), 400)
    Ls, Ld = arclen(src), arclen(dst)
    Ts, Ns, Bs = frames(src)
    Td, Nd, Bd = frames(dst)
    out = X.copy()
    thick = cfg.get('thick', 1.0)
    blend = cfg.get('blend', 0.08)
    rep = {'src_len': float(Ls[-1]), 'dst_len': float(Ld[-1]), 'bands': len(cents)}
    for i, p in zip(ids, Q):
        j = int(np.argmin(((src - p) ** 2).sum(1)))
        s = Ls[j] / Ls[-1]
        d = p - src[j]
        dt, dn, db = d @ Ts[j], d @ Ns[j], d @ Bs[j]
        k = int(np.searchsorted(Ld / Ld[-1], s))
        k = min(k, len(dst) - 1)
        q = dst[k] + Td[k] * dt * (Ld[-1] / Ls[-1]) + (Nd[k] * dn + Bd[k] * db) * thick
        w = np.clip(Ls[j] / (Ls[-1] * blend), 0, 1)
        w = w * w * (3 - 2 * w)
        out[i] = p * (1 - w) + q * w
    return out, rep
