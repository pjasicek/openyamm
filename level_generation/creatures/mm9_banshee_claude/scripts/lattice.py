"""Cloak and dress as smooth surfaces on MM9's own chains (numpy only, also imported inside Blender).
MM9's cloth is a 43-vertex envelope and its dress a 50-vertex tube, every vertex rigid on one chain joint. The joints sit on the surface, so they are a lattice: the surface is a cubic through the lattice,
the weights are bilinear hats on it. The cloth follows MM9's motion exactly, without MM9's facets. Coordinates: MM9 metres, x right of the image, y back, z up (raw ABC side: 01 chains at +x).
J = {bone: rest head (3,)}."""
import numpy as np


def catmull(P, t, closed=False):
    """P (n, 3) control points, t floats in 0..n-1 (0..n when closed): centripetal-free uniform Catmull-Rom"""
    n = len(P)
    t = np.asarray(t, float)
    if closed:
        i = np.floor(t).astype(int) % n; f = t - np.floor(t)
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
    else:
        i = np.clip(np.floor(t).astype(int), 0, n - 2); f = t - i
        ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
    f = f[..., None]
    return 0.5 * (2 * p1 + (p2 - p0) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f ** 2 + (3 * p1 - p0 - 3 * p2 + p3) * f ** 3)


def resample_arc(pts, ns):
    """ns points at equal arc steps along a Catmull-Rom through pts, and their position in joint units"""
    t = np.linspace(0, len(pts) - 1, 200)
    C = catmull(pts, t)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    q = np.linspace(0, s[-1], ns)
    tq = np.interp(q, s, t)
    return catmull(pts, tq), tq


# ------------------------------------------------------------------ cloak: half lattice, centre (c=0) to the wrist (c=4); rows root, mid, end, tip
def cloak_lattice(J, mid_centre, mid_b, mid_c, roots):
    """left = -x columns (no suffix); the +x side mirrors them onto the 01 bones."""
    cols = []
    bones = []
    cols.append([roots['c'], mid_centre, J['Xcend'], J['Xctip']]); bones.append([['Xspine2'], ['Xcmid'], ['Xcend'], ['Xctip']])
    a_mid = 0.5 * (mid_centre + mid_b); a_mid[1] = 0.5 * (a_mid[1] + J['XcAend'][1] * 0.45)
    cols.append([roots['a'], a_mid, J['XcAend'], J['XcAtip']]); bones.append([['Xspine2'], ['Xcmid', 'XcBmid'], ['XcAend'], ['XcAtip']])
    cols.append([roots['b'], mid_b, J['XcBend'], J['XcBtip']]); bones.append([['Zarmpiv'], ['XcBmid'], ['XcBend'], ['XcBtip']])
    cols.append([roots['e'], mid_c, J['XcCend'], J['XcCtip']]); bones.append([['Zarmpiv', 'Zarm'], ['XcCmid'], ['XcCend'], ['XcCtip']])
    cols.append([roots['w'], J['XcDmid'], J['XcDend'], J['XcDtip']]); bones.append([['Zarm'], ['XcDmid'], ['XcDend'], ['XcDtip']])
    return np.array(cols, float), bones


def mirror_bone(n):
    side = {'Xcmid': 'Xcmid', 'Xcend': 'Xcend', 'Xctip': 'Xctip', 'Xspine2': 'Xspine2'}
    return side.get(n, n + '01')


def cloak_grid(L, bones, nu_half=20, nv=13):
    """Returns co (nv, 2nu_half+1, 3), weights list per vertex {bone: w}, uv (u 0 centre..1 wrist per side, v 0 root..1 tip), side (-1,0,+1)"""
    nc, nr = L.shape[:2]
    # full lattice: wrist(-x) ... centre ... wrist(+x)
    Lf = np.concatenate([L[::-1], L[1:] * np.array([-1, 1, 1])], 0)
    vs = np.linspace(0, nr - 1, nv)
    us_half = np.linspace(0, nc - 1, nu_half + 1)
    us = np.r_[-us_half[::-1][:-1], us_half] + (nc - 1)
    co = np.zeros((nv, len(us), 3))
    # along v per lattice column, then across u per v
    ColV = np.stack([catmull(Lf[c], vs) for c in range(Lf.shape[0])], 0)   # (cols, nv, 3)
    for r in range(nv):
        co[r] = catmull(ColV[:, r], us)
    W = []
    for r in range(nv):
        row = []
        v = vs[r]
        # classic skinning: a bone owns the segment to its child, joints blend (a chain's tip bone carries nothing: it has no child and MM9 turns it freely)
        bv = max(v - 0.5, 0.0); r0 = min(int(bv), nr - 3); fv = min(bv - r0, 1.0)
        for k, u in enumerate(us):
            uh = abs(u - (nc - 1))
            c0 = min(int(uh), nc - 2); fu = uh - c0
            d = {}
            for (c, a) in ((c0, 1 - fu), (c0 + 1, fu)):
                for (rr, b) in ((r0, 1 - fv), (r0 + 1, fv)):
                    w = a * b
                    if w < 1e-6:
                        continue
                    names = bones[c][rr]
                    for nm in names:
                        d[nm] = d.get(nm, 0) + w / len(names)
            row.append(d)
        W.append(row)
    uv = np.stack(np.meshgrid(np.abs(us - (nc - 1)) / (nc - 1), vs / (nr - 1)), -1)
    return co, W, uv, np.sign(us - (nc - 1))


def mirrored_weights(W, sides):
    """side +1 columns use 01 bones"""
    out = []
    for row in W:
        r = []
        for d, s in zip(row, sides):
            if s > 0:
                r.append({mirror_bone(k): v for k, v in d.items()})
            elif s == 0:
                # the centre column: wherever a side bone reaches it, it splits
                dd = {}
                for k, v in d.items():
                    m = mirror_bone(k)
                    dd[k] = dd.get(k, 0) + v / 2; dd[m] = dd.get(m, 0) + v / 2
                r.append(dd)
            else:
                r.append(d)
        out.append(r)
    return out


# ------------------------------------------------------------------ dress: periodic columns, front -> left(+x, bones without 01 side in this data: Yl = +x) -> back -> right -> front
SKIRT_CHAINS = [
    ['Yfront', 'YfB', 'YfC', 'YfD', 'YfE'],
    ['Yfrontleft', 'YflA', 'YflB', 'YflC'],
    ['Yleft', 'YlA', 'YlB', 'YlC', 'YlD', 'YlE'],
    ['Ybackleft', 'YblA', 'YblB', 'YblC', 'YblD'],
    ['Yback', 'YbB', 'YbC', 'YbD', 'YbE'],
    ['Ybackrit', 'YbrA', 'YbrB', 'YbrC', 'YbrD'],
    ['Yrit', 'YrA', 'YrB', 'YrC', 'YrD', 'YrE'],
    ['Yfrontrit', 'YfrA', 'YfrB', 'YfrC'],
]


def skirt_grid(J, top, nt=48, ns=22):
    """top: (8, 3) the waist ring points the columns start from (the belt line on our torso). Columns run from there through their joints to the hem.
    Returns co (ns, nt, 3), W, st (theta 0..1 periodic, s 0..1). The chains with their first joint low (frontleft/right) also start at the waist."""
    cols = []; ts = []
    for c, ch in enumerate(SKIRT_CHAINS):
        pts = np.array([J[n] for n in ch])
        keep = pts[:, 2] < top[c, 2] - 0.02
        pts2 = np.vstack([top[c], pts[keep]])
        C, tq = resample_arc(pts2, ns)
        cols.append(C)
        # joint fraction: map to the chain's joints (with the waist point standing for the first kept joint's parent)
        idx = np.where(keep)[0]
        names = [ch[max(idx[0] - 1, 0)]] + [ch[i] for i in idx]
        ts.append((tq, names))
    cols = np.array(cols)            # (8, ns, 3)
    us = np.linspace(0, 8, nt, endpoint=False)
    co = np.zeros((ns, nt, 3))
    for r in range(ns):
        co[r] = catmull(cols[:, r], us, closed=True)
    W = []
    for r in range(ns):
        row = []
        for u in us:
            c0 = int(u) % 8; c1 = (c0 + 1) % 8; f = u - int(u)
            d = {}
            for c, a in ((c0, 1 - f), (c1, f)):
                if a < 1e-6:
                    continue
                tq, names = ts[c]
                # classic skinning, as the cloak; the chain's last joint carries nothing
                t = max(tq[r] - 0.5, 0.0); j0 = min(int(t), len(names) - 3); g = min(t - j0, 1.0)
                for nm, b in ((names[j0], 1 - g), (names[j0 + 1], g)):
                    if a * b > 1e-6:
                        d[nm] = d.get(nm, 0) + a * b
            # the belt band rides XCENTER with the torso's waist
            ws = r / (ns - 1)
            k = 1 - min(max((ws - 0.015) / 0.09, 0.0), 1.0); k = k * k * (3 - 2 * k)
            if k > 0:
                d = {n: x * (1 - k) for n, x in d.items()}
                d['XCENTER'] = d.get('XCENTER', 0) + k
            row.append(d)
        W.append(row)
    st = np.stack(np.meshgrid(us / 8, np.linspace(0, 1, ns)), -1)
    return co, W, st
