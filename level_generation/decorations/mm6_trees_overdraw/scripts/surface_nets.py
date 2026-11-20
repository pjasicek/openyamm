"""Surface nets (numpy): a closed quad mesh of the zero level set of a sampled scalar field (negative inside).
One vertex per grid cell the surface crosses (the mean of its edge crossings), one quad per crossed grid edge joining
the four cells around it, wound so that the quads face outward (toward positive values)."""
import numpy as np


def mesh(field, origin, step):
    """field (nx, ny, nz) sampled at origin + step * (i, j, k). Returns verts (n, 3), quads (m, 4)."""
    f = np.asarray(field, np.float64)
    nx, ny, nz = f.shape
    inside = f < 0
    # cell corner signs
    corners = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
    cs = np.stack([inside[i:nx - 1 + i, j:ny - 1 + j, k:nz - 1 + k] for i, j, k in corners], -1)
    active = cs.any(-1) & ~cs.all(-1)
    cell_id = -np.ones(active.shape, np.int64)
    cell_id[active] = np.arange(int(active.sum()))
    # vertex per active cell: mean of the crossing points on its 12 edges
    acc = np.zeros(active.shape + (3,)); cnt = np.zeros(active.shape)
    edges = [((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0)), ((0, 0, 1), (1, 0, 1)), ((0, 1, 1), (1, 1, 1)),
             ((0, 0, 0), (0, 1, 0)), ((1, 0, 0), (1, 1, 0)), ((0, 0, 1), (0, 1, 1)), ((1, 0, 1), (1, 1, 1)),
             ((0, 0, 0), (0, 0, 1)), ((1, 0, 0), (1, 0, 1)), ((0, 1, 0), (0, 1, 1)), ((1, 1, 0), (1, 1, 1))]
    for a, b in edges:
        fa = f[a[0]:nx - 1 + a[0], a[1]:ny - 1 + a[1], a[2]:nz - 1 + a[2]]
        fb = f[b[0]:nx - 1 + b[0], b[1]:ny - 1 + b[1], b[2]:nz - 1 + b[2]]
        cross = (fa < 0) != (fb < 0)
        t = np.where(cross, fa / np.where(cross, fa - fb, 1.0), 0.0)
        p = np.array(a, float) + t[..., None] * (np.array(b, float) - np.array(a, float))
        acc += np.where(cross[..., None], p, 0.0); cnt += cross
    idx = np.argwhere(active)
    local = acc[active] / np.maximum(cnt[active], 1)[:, None]
    verts = np.asarray(origin) + (idx + local) * step
    quads = []
    # grid edges along x between (i, j, k) and (i+1, j, k): cells (i, j-1..j, k-1..k)
    for axis in range(3):
        sl0 = [slice(None)] * 3; sl1 = [slice(None)] * 3
        sl0[axis] = slice(0, -1); sl1[axis] = slice(1, None)
        cross = inside[tuple(sl0)] != inside[tuple(sl1)]
        out_dir = inside[tuple(sl0)]          # inside -> outside along +axis: normal points +axis
        e = np.argwhere(cross)
        u, v = [x for x in range(3) if x != axis]
        ok = (e[:, u] >= 1) & (e[:, v] >= 1) & (e[:, u] <= active.shape[u]) & (e[:, v] <= active.shape[v])
        ok &= e[:, axis] < active.shape[axis]
        e = e[ok]; flip = out_dir[tuple(e.T)]
        offs = [(0, 0), (1, 0), (1, 1), (0, 1)]
        q = []
        for du, dv in offs:
            c = e.copy(); c[:, u] -= 1 - du; c[:, v] -= 1 - dv
            valid = (c[:, u] >= 0) & (c[:, v] >= 0) & (c[:, u] < active.shape[u]) & (c[:, v] < active.shape[v])
            c = np.clip(c, 0, np.array(active.shape) - 1)
            q.append(np.where(valid, cell_id[tuple(c.T)], -1))
        q = np.stack(q, 1)
        # (u, v, axis) right-handed: counter-clockwise in (u, v) faces +axis when (u, v, axis) is a cyclic order
        cyclic = (u, v, axis) in ((0, 1, 2), (1, 2, 0), (2, 0, 1))
        rev = flip != cyclic
        q[rev] = q[rev][:, ::-1]
        quads.append(q[(q >= 0).all(1)])
    quads = np.concatenate(quads)
    return verts, quads
