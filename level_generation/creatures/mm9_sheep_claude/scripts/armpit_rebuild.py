#!/usr/bin/env python3
"""Rebuild the brisket/armpit skin of the wolf as one clean surface (system python: numpy + scipy). 2026-10-30.

Why: below the chest the voxel body keeps a thin keel of fused chest fur hanging between the forelegs, joined to the
inner legs by thin pinched webs at the front, with deep narrow slots (armpit notches) behind them. The webs tear into
a loose sheet with background gaps when a leg swings (rearing bite, walk), and the slot rims give a hard crease.

How (topology and UVs are kept; only positions in the region move, so the texture carries over without a seam):
1. Inside/outside of the closed skin on a grid over the region (ray parity along z).
2. Below Z_CUT each z slice keeps only the parts that hold a foreleg axis point (after a small 2D opening that
   breaks the webs): the keel goes. A 3D closing (ball CLOSE_R) fills the narrow notches behind the elbows; near
   the grid border the volume is unchanged.
3. A smooth signed distance of the result is the target surface.
4. Region = skin vertices off the target by more than TOL, grown by RINGS edge rings (the outer ring is the fixed
   boundary). Iterate: Laplacian step in the region, Newton projection onto the target, so the old keel, web and
   slot faces spread over the new surface without folds.

Args: <dump npz (dump_weights.py)> <out npz: P> [report json]; untangles (weight_refine.untangle) before and after.
"""
import sys, json
import numpy as np
from scipy import ndimage

BOX = (-0.42, 0.42, -0.8, 0.2, 0.62, 1.32)     # Blender world: x, y, z ranges (brisket and both armpits)
H = 0.005                                      # grid step, model units
Z_CUT = 0.95          # below this, slice parts that hold no leg axis (the keel) are removed
WEB_R = 0.02          # per-slice opening that breaks the thin webs before the parts are told apart
CLOSE_R = 0.06        # 3D closing that fills the notches and pockets behind the elbows (mouths up to ~0.1)
LEGS = (('Bone11', 'Bone12'), ('Bone16', 'Bone17'))
TOL = 0.004
RINGS = 3
ITERS = 60
BLUR = 3.0            # voxels: gaussian on the signed distance, a fillet where the legs meet the chest


def inside_grid(co, tris, box, h):
    xs = np.arange(box[0], box[1] + h / 2, h)
    ys = np.arange(box[2], box[3] + h / 2, h)
    zs = np.arange(box[4] - 0.3, box[5] + 0.3 + h / 2, h)     # extra z so parity starts outside
    hits = {}
    for t in tris:
        p = co[t]
        x0, x1 = p[:, 0].min(), p[:, 0].max()
        y0, y1 = p[:, 1].min(), p[:, 1].max()
        i0, i1 = np.searchsorted(xs, x0), np.searchsorted(xs, x1, 'right')
        j0, j1 = np.searchsorted(ys, y0), np.searchsorted(ys, y1, 'right')
        if i0 >= i1 or j0 >= j1:
            continue
        X, Y = np.meshgrid(xs[i0:i1], ys[j0:j1], indexing='ij')
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-14:
            continue
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / d
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / d
        l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        for ii, jj, zz in zip(*np.nonzero(m), z[m]):
            hits.setdefault((i0 + ii, j0 + jj), []).append(zz)
    inside = np.zeros((len(xs), len(ys), len(zs)), bool)
    for (i, j), zl in hits.items():
        zl = np.sort(zl)
        for k in range(0, len(zl) - 1, 2):
            inside[i, j, (zs >= zl[k]) & (zs < zl[k + 1])] = True
    return inside, (xs[0], ys[0], zs[0])


def ball(r, h):
    n = int(np.ceil(r / h))
    g = np.arange(-n, n + 1)
    X, Y, Z = np.meshgrid(g, g, g, indexing='ij')
    return (X * X + Y * Y + Z * Z) * h * h <= r * r


def disk(r, h):
    n = int(np.ceil(r / h))
    g = np.arange(-n, n + 1)
    X, Y = np.meshgrid(g, g, indexing='ij')
    return (X * X + Y * Y) * h * h <= r * r


def remove_keel(inside, origin, h, legs, z_cut, web_r):
    """Below z_cut keep, per z slice, only the parts that hold a leg axis point (legs: [(head, child head)])."""
    vol = inside.copy()
    nz = inside.shape[2]
    for k in range(nz):
        z = origin[2] + k * h
        if z >= z_cut or not inside[:, :, k].any():
            continue
        sl = inside[:, :, k]
        op = ndimage.binary_opening(sl, disk(web_r, h))
        lab, n = ndimage.label(op)
        keep = np.zeros(n + 1, bool)
        for a, b in legs:
            t = (z - a[2]) / (b[2] - a[2])
            q = a + t * (b - a)
            i, j = int(round((q[0] - origin[0]) / h)), int(round((q[1] - origin[1]) / h))
            if 0 <= i < sl.shape[0] and 0 <= j < sl.shape[1]:
                # the nearest labelled part to the axis point
                if lab[i, j]:
                    keep[lab[i, j]] = True
                else:
                    ii, jj = np.nonzero(lab)
                    if len(ii):
                        m = np.argmin((ii - i) ** 2 + (jj - j) ** 2)
                        keep[lab[ii[m], jj[m]]] = True
        kept = keep[lab]
        vol[:, :, k] = ndimage.binary_dilation(kept, disk(web_r, h)) & sl
    return vol


def target_sdf(inside, origin, h, legs, z_cut, web_r, close_r):
    vol = remove_keel(inside, origin, h, legs, z_cut, web_r)
    vol = ndimage.binary_closing(vol, ball(close_r, h))
    # keep the original volume near the grid border (the region fades into the untouched body)
    border = np.ones(inside.shape, bool)
    pad = int(np.ceil(close_r / h)) + 2
    border[pad:-pad, pad:-pad, pad:-pad] = False
    vol[border] = inside[border]
    sdf = ndimage.distance_transform_edt(~vol) * h - ndimage.distance_transform_edt(vol) * h
    return ndimage.gaussian_filter(sdf, BLUR), vol


def sample(f, origin, h, pts):
    idx = ((pts - np.array(origin)) / h).T
    return ndimage.map_coordinates(f, idx, order=1, mode='nearest')


def grad(f, origin, h, pts):
    e = h
    g = np.zeros_like(pts)
    for k in range(3):
        d = np.zeros(3)
        d[k] = e
        g[:, k] = (sample(f, origin, h, pts + d) - sample(f, origin, h, pts - d)) / (2 * e)
    return g


def rebuild(co, tris, piece, legs, box=BOX, h=H, z_cut=Z_CUT, web_r=WEB_R, close_r=CLOSE_R, tol=TOL, rings=RINGS,
            iters=ITERS):
    """legs: [(root head, child head)] in Blender world."""
    skin = tris[(piece[tris] == 0).all(1)]
    inside, origin = inside_grid(co, skin, box, h)
    f, vol = target_sdf(inside, origin, h, legs, z_cut, web_r, close_r)
    n = len(co)
    E = np.unique(np.sort(np.concatenate([skin[:, [0, 1]], skin[:, [1, 2]], skin[:, [2, 0]]]), 1), axis=0)
    inb = (piece == 0) & (co[:, 0] > box[0]) & (co[:, 0] < box[1]) & (co[:, 1] > box[2]) & (co[:, 1] < box[3]) \
        & (co[:, 2] > box[4]) & (co[:, 2] < box[5])
    off = np.zeros(n)
    off[inb] = sample(f, origin, h, co[inb])
    reg = inb & (np.abs(off) > tol)
    core = reg.copy()
    for _ in range(rings):
        g = reg.copy()
        g[E[reg[E[:, 0]], 1]] = True
        g[E[reg[E[:, 1]], 0]] = True
        reg = g & inb
    deg = np.zeros(n)
    np.add.at(deg, E[:, 0], 1)
    np.add.at(deg, E[:, 1], 1)
    p = co.copy()
    ri = np.nonzero(reg)[0]
    for _ in range(iters):
        acc = np.zeros_like(p)
        np.add.at(acc, E[:, 0], p[E[:, 1]])
        np.add.at(acc, E[:, 1], p[E[:, 0]])
        p[ri] += 0.5 * (acc[ri] / deg[ri, None] - p[ri])
        for _ in range(2):
            v = sample(f, origin, h, p[ri])
            g = grad(f, origin, h, p[ri])
            p[ri] -= (v / np.maximum((g * g).sum(1), 1e-9))[:, None] * g
    mv = np.linalg.norm(p - co, axis=1)
    rep = {'grid': list(inside.shape), 'removed_voxels': int((inside & ~vol).sum()),
           'added_voxels': int((vol & ~inside).sum()), 'off_target_verts': int(core.sum()),
           'region_verts': int(reg.sum()), 'max_move': round(float(mv.max()), 4),
           'mean_move_region': round(float(mv[reg].mean()), 4) if reg.any() else 0.0,
           'residual_max': round(float(np.abs(sample(f, origin, h, p[ri])).max()), 4) if reg.any() else 0.0}
    return p, rep, reg


if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import weight_refine as R
    d = np.load(sys.argv[1])
    bones = [str(b) for b in d['bones']]
    legs = [(d['heads'][bones.index(a)], d['heads'][bones.index(b)]) for a, b in LEGS]
    P0, urep = R.untangle(d['co'], d['tris'], d['piece'])
    if '--offsets' in sys.argv:
        # only the target offsets at the untangled rest positions (armpit_patch.py cuts and refills the pockets)
        skin = d['tris'][(d['piece'][d['tris']] == 0).all(1)]
        inside, origin = inside_grid(P0, skin, BOX, H)
        f, vol = target_sdf(inside, origin, H, legs, Z_CUT, WEB_R, CLOSE_R)
        inb = (d['piece'] == 0) & (P0[:, 0] > BOX[0]) & (P0[:, 0] < BOX[1]) & (P0[:, 1] > BOX[2]) \
            & (P0[:, 1] < BOX[3]) & (P0[:, 2] > BOX[4]) & (P0[:, 2] < BOX[5])
        off = np.zeros(len(P0))
        off[inb] = sample(f, origin, H, P0[inb])
        np.savez(sys.argv[2], P=P0, off=off)
        print('OFFSETS', json.dumps({'untangle': urep, 'inside_target': int((off < -TOL).sum()),
                                     'outside_target': int((off > TOL).sum())}))
        sys.exit(0)
    P, rep, reg = rebuild(P0, d['tris'], d['piece'], legs)
    P, urep2 = R.untangle(P, d['tris'], d['piece'])
    rep['untangle_before'] = urep
    rep['untangle_after'] = urep2
    np.savez(sys.argv[2], P=P, region=reg)
    if len(sys.argv) > 3:
        json.dump(rep, open(sys.argv[3], 'w'), indent=1)
    print('ARMPIT ' + json.dumps(rep))
