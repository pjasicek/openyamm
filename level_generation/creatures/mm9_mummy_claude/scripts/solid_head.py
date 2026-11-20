"""Solid closed head from the double-walled Meshy surface: voxelise the surface, flood the outside, marching cubes on the blurred solid.
Args: <head_raw.npz> <out npz>"""
import sys
import numpy as np
from scipy import ndimage as ni


def surface_nets(f, iso):
    """Naive surface nets, quads split into triangles. Returns verts in grid units and triangles."""
    b = f > iso
    nx, ny, nz = f.shape
    # active cells
    c = b[:-1, :-1, :-1].astype(np.int8) + b[1:, :-1, :-1] + b[:-1, 1:, :-1] + b[:-1, :-1, 1:] + b[1:, 1:, :-1] + b[1:, :-1, 1:] + b[:-1, 1:, 1:] + b[1:, 1:, 1:]
    act = (c > 0) & (c < 8)
    ids = -np.ones(act.shape, np.int64); ids[act] = np.arange(act.sum())
    ci = np.argwhere(act)
    acc = np.zeros((len(ci), 3)); cnt = np.zeros(len(ci))
    corners = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]])
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    fc = np.stack([f[ci[:, 0] + d[0], ci[:, 1] + d[1], ci[:, 2] + d[2]] for d in corners], 1)
    for a, e in edges:
        fa, fb = fc[:, a], fc[:, e]
        m = (fa > iso) != (fb > iso)
        u = (iso - fa[m]) / (fb[m] - fa[m])
        acc[m] += corners[a] + (corners[e] - corners[a]) * u[:, None]; cnt[m] += 1
    v = ci + acc / cnt[:, None]
    tris = []
    # axis-aligned grid edges crossing: one quad of the four cells around each
    for ax in range(3):
        o = [(ax + 1) % 3, (ax + 2) % 3]
        sl0 = [slice(None)] * 3; sl1 = [slice(None)] * 3
        sl0[ax] = slice(None, -1); sl1[ax] = slice(1, None)
        cross = b[tuple(sl0)] != b[tuple(sl1)]
        idx = np.argwhere(cross)
        idx = idx[(idx[:, o[0]] > 0) & (idx[:, o[1]] > 0) & (idx[:, o[0]] < f.shape[o[0]] - 1) & (idx[:, o[1]] < f.shape[o[1]] - 1)]
        def cid(da, db):
            q = idx.copy(); q[:, o[0]] -= da; q[:, o[1]] -= db
            return ids[q[:, 0], q[:, 1], q[:, 2]]
        a, b2, c2, d = cid(1, 1), cid(0, 1), cid(0, 0), cid(1, 0)
        flip = b[tuple(idx.T)]
        q = np.stack([a, b2, c2, d], 1)
        q[flip] = q[flip][:, ::-1]
        tris.append(q[:, [0, 1, 2]]); tris.append(q[:, [0, 2, 3]])
    return v, np.vstack(tris)
D = np.load(sys.argv[1]); co, tri = D['co'], D['tri']
# chin spike
keep = ~((co[:, 2] < -0.125) & (co[:, 1] < -0.085))
tri = tri[keep[tri].all(1)]
h = 0.0035
lo = co.min(0) - 6 * h; dims = np.ceil((co.max(0) - co.min(0)) / h).astype(int) + 13
S = np.zeros(dims, bool)
# dense surface samples
A, B, C = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
L = np.maximum.reduce([np.linalg.norm(A - B, axis=1), np.linalg.norm(B - C, axis=1), np.linalg.norm(C - A, axis=1)])
for i in range(len(tri)):
    n = int(np.ceil(L[i] / (h * 0.6))) + 1
    u, v = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n)); m = u + v <= 1
    p = A[i] + np.outer(u[m], B[i] - A[i]) + np.outer(v[m], C[i] - A[i])
    q = ((p - lo) / h).astype(int)
    S[q[:, 0], q[:, 1], q[:, 2]] = True
print('surface voxels', S.sum(), dims)
CL = 6
d = ni.binary_dilation(S, iterations=CL)
out, n = ni.label(~d)
border = np.unique(np.r_[out[0].ravel(), out[-1].ravel(), out[:, 0].ravel(), out[:, -1].ravel(), out[:, :, 0].ravel(), out[:, :, -1].ravel()])
outside = np.isin(out, border[border > 0])
solid = ~outside
solid = ni.binary_fill_holes(solid)
solid = ni.binary_erosion(solid, iterations=CL)
# wisps
lab, n = ni.label(solid); solid = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
inv, n = ni.label(~solid)
sz = np.bincount(inv.ravel()); big = sz[1:].argmax() + 1
solid |= (inv != big)
f = ni.gaussian_filter(solid.astype(np.float32), 1.1)
v, t = surface_nets(f, 0.5)
v = v * h + lo
np.savez(sys.argv[2], co=v, tri=t)
print('MC', len(v), len(t), v.min(0), v.max(0))
