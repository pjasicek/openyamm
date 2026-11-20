#!/usr/bin/env python3
"""Mouth and nose reshape (user, 2026-11-01: "mouth too thin, nose too tall and thin"; look authority the HD master
references_hd/01_front.png and MM9's head). Meshy's face had a 1.7 cm pursed mouth (0.36 of the eye spacing; master and
MM9 about 0.7) and a 1 cm pinched nose (0.2; master and MM9 0.4-0.5) with its base 0.95 eye spacings below the eyes
(MM9 0.8). Vertex moves only, after subdiv_face.py (UVs and weights kept, so the projected paint moves with the skin;
project_head.py still projects on the unshaped head: work/mesh_sub.npz -> dump_head.py).
- mouth: wider by a horizontal displacement that rises across the lips and gives back over the cheek (zero net, the face
  outline is unchanged), corners from 8.6 to ~17 mm; points follow the face's own front surface (measured per height);
  upper lip 1.6x and lower lip 1.35x taller around the mouth line and the lower lip a little fuller;
- nose: wings and bridge wider by the same kind of displacement (wings 5 -> ~8.5 mm), base and tip lifted 4 mm (shorter
  nose, the bridge above takes the compression, the upper lip the stretch).
make_field() is shared with project_head.py, which samples the paint at the field's smooth inverse (no kinks at triangle
edges, which the frozen UVs gave when the paint simply rode on the moved vertices). Fields act only on head-material skin and mouth vertices in front of the face (y < 0.01, fading out by y 0.04). Args: <in npz> <out npz>"""
import sys
import numpy as np
from scipy.interpolate import RegularGridInterpolator


ZMOUTH = 0.832       # lip junction on the midline (section: upper lip front at 0.835, lower lip front 0.827, nose base 0.847)


def ss(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def profile(knots, slope, target_u, target_d):
    """displacement D(u), u >= 0, from a slope table (D' at knots, linear between), net zero, scaled so D(target_u) = target_d"""
    u = np.linspace(0, knots[-1], 2001); s = np.interp(u, knots, slope)
    pos, neg = np.clip(s, 0, None), np.clip(s, None, 0)
    neg = neg * (np.trapezoid(pos, u) / max(-np.trapezoid(neg, u), 1e-12))
    Dc = np.concatenate([[0], np.cumsum((pos + neg)[1:] + (pos + neg)[:-1]) * 0.5 * (u[1] - u[0])])
    Dc = Dc * target_d / np.interp(target_u, u, Dc)
    return lambda q: np.interp(q, u, Dc, right=0.0)


def make_field(D):
    """displacement function disp(P) -> (n, 3) for points P (mesh space or the head's true-handed space: x enters as |x|)"""
    co, tri, mat, comp = D['co'], D['tri'], D['mat'], D['comp']; mn = [str(x) for x in D['matnames']]
    # the face's front surface per height, Y(|x|, z): front-most skin per 1 mm column in 3 mm bands, measured from 9 mm out;
    # inside 9 mm (lips, nose) a quadratic with the same value and slope at 9 mm, so the lips keep their own protrusion
    skin = np.unique(tri[mat == mn.index('EboraHead')]); skin = skin[comp[skin] == 0]; S = co[skin]; S = S[S[:, 1] < 0.03]
    XG = np.arange(0.0, 0.0505, 0.001); ZG = np.arange(0.800, 0.902, 0.003); X0 = 0.009
    YT = np.zeros((len(ZG), len(XG)))
    for i, zc in enumerate(ZG):
        b_ = np.abs(S[:, 2] - zc) < 0.003; ax_, ys = np.abs(S[b_, 0]), S[b_, 1]
        col = np.full(len(XG), np.nan)
        for j, xc in enumerate(XG):
            m = np.abs(ax_ - xc) < 0.0012
            if m.any(): col[j] = ys[m].min()
        ok = ~np.isnan(col); col = np.interp(XG, XG[ok], col[ok])
        col = np.convolve(np.pad(col, 2, mode='edge'), np.ones(5) / 5, mode='valid')
        j0 = int(round(X0 / 0.001)); slope = (col[j0 + 2] - col[j0 - 2]) / 0.004; bq = max(slope, 0) / (2 * X0)
        col[:j0] = col[j0] + bq * (XG[:j0] ** 2 - X0 ** 2)
        YT[i] = col
    RI = RegularGridInterpolator((ZG, XG), YT, bounds_error=False, fill_value=None)
    Ysurf = lambda a, z_: RI(np.c_[np.clip(z_, ZG[0], ZG[-1]), np.clip(a, 0, XG[-1])])
    ZM = ZMOUTH
    # mouth width: corners 8.6 -> ~17 mm at the mouth line
    Dm = profile([0, 0.006, 0.011, 0.016, 0.035, 0.050, 0.055], [1.1, 1.0, 0.3, -0.3, -0.2, 0, 0], 0.0086, 0.0084)
    # lips taller around the mouth line: lower 1.35x, upper 1.6x, less at the corners; no stretch at the junction itself
    # (stretching from the junction pulled the lips apart over inner faces no view had painted: a pale slit)
    Dv = profile([0, 0.0015, 0.004, 0.007, 0.010, 0.016, 0.022, 0.025], [0.0, 0.5, 0.40, 0.0, -0.3, -0.15, 0, 0], 0.005, 0.0014)
    Du = profile([0, 0.0015, 0.005, 0.008, 0.011, 0.017, 0.022, 0.025], [0.0, 0.8, 0.6, 0.0, -0.3, -0.15, 0, 0], 0.006, 0.0030)
    # nose width: wings 5 -> ~8.5 mm, bridge less, nothing at the brow
    Dn = profile([0, 0.004, 0.008, 0.012, 0.020, 0.030, 0.034], [0.9, 0.8, 0.2, -0.3, -0.25, 0, 0], 0.005, 0.0035)

    def disp(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]; ax = np.abs(x); sg = np.sign(x)
        front = ss((0.040 - y) / 0.030)        # full in front of y 1 cm (the cheeks beside the mouth reach 0.8 cm), none behind 4 cm
        gm = np.exp(-((z - ZM) / 0.0095) ** 2)
        dxm = sg * Dm(ax) * gm * front
        dzm = np.where(z > ZM, Du(np.abs(z - ZM)), -Dv(np.abs(z - ZM))) * np.exp(-(ax / 0.022) ** 2) * front
        # lower lip a touch fuller (forward), upper lip body likewise less
        lower = np.exp(-((z - (ZM - 0.0042)) / 0.0028) ** 2) * np.exp(-(ax / 0.012) ** 2)
        upper = np.exp(-((z - (ZM + 0.0045)) / 0.0028) ** 2) * np.exp(-(ax / 0.012) ** 2)
        dym = -(0.0014 * lower + 0.0006 * upper) * front
        bz = np.interp(z, [0.832, 0.840, 0.846, 0.856, 0.870, 0.884, 0.895], [0, 0.35, 1.0, 1.0, 0.55, 0.3, 0])
        dxn = sg * Dn(ax) * bz * front
        # nose shorter: base and tip up 4 mm, the bridge above compressed, the upper lip stretched
        rz = np.where(z >= 0.852, ss((0.884 - z) / 0.032), np.where(z >= 0.846, 1.0, ss((z - 0.836) / 0.010)))
        dzn = 0.004 * rz * np.exp(-(ax / 0.016) ** 2) * front
        dx = dxm + dxn
        dyf = (Ysurf(np.abs(x + dx), z) - Ysurf(ax, z)) * np.clip(gm + bz * ss((ax - 0.006) / 0.008), 0, 1)
        dy = np.clip(dyf, -1.5 * np.abs(dx), 1.5 * np.abs(dx)) + dym      # on the steep jaw sides the slide is capped (it squashed faces)
        return np.c_[dx, dy, dzm + dzn]
    return disp


def inverse(disp, Q, it=40):
    """points P with P + disp(P) = Q (damped fixed point; the field's slope stays within 0.5-2.2)"""
    P = Q.copy()
    for _ in range(it):
        P = P + 0.5 * (Q - (P + disp(P)))
    return P, float(np.abs(P + disp(P) - Q).max())


if __name__ == '__main__':
    D = dict(np.load(sys.argv[1])); co = D['co'].copy(); tri, mat, comp = D['tri'], D['mat'], D['comp']
    mn = [str(x) for x in D['matnames']]
    hv = np.unique(tri[mat == mn.index('EboraHead')]); hv = hv[np.isin(comp[hv], (0, 9))]
    P = co[hv]; d = make_field(D)(P)
    co[hv] = P + d
    # the pursed mouth's radial pucker folds (upper lip most) read as a dark zigzag once widened: Taubin smoothing of the lips
    # (welded by position, faded at the zone's edge, mouth interior part 9 included), 12 passes
    key = np.round(co, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); nW = inv.max() + 1
    th = tri[mat == mn.index('EboraHead')]; e = np.r_[th[:, [0, 1]], th[:, [1, 2]], th[:, [2, 0]]]; e = inv[e]
    e = np.unique(np.sort(e, 1), axis=0); e = e[e[:, 0] != e[:, 1]]
    Wp = np.zeros((nW, 3)); np.add.at(Wp, inv, co); cnt = np.bincount(inv, minlength=nW)[:, None]; Wp = Wp / np.maximum(cnt, 1)
    hvW = np.unique(inv[hv]); zx = np.zeros(nW)
    q = Wp[hvW]; ZM_ = ZMOUTH
    zx[hvW] = (ss((0.021 - np.abs(q[:, 0])) / 0.005) * np.where(q[:, 2] > ZM_, ss((ZM_ + 0.0095 - q[:, 2]) / 0.003), ss((q[:, 2] - (ZM_ - 0.008)) / 0.003))
               * ss((0.0 - q[:, 1]) / 0.004) * np.where(q[:, 2] > ZM_, 1.0, 0.6))
    deg = np.bincount(e.ravel(), minlength=nW)[:, None]
    def lap(X):
        A = np.zeros_like(X); np.add.at(A, e[:, 0], X[e[:, 1]]); np.add.at(A, e[:, 1], X[e[:, 0]]); return A / np.maximum(deg, 1) - X
    X = Wp.copy()
    for _ in range(12):
        X = X + 0.5 * zx[:, None] * lap(X); X = X - 0.53 * zx[:, None] * lap(X)
    sm = X - Wp; co = co + sm[inv]
    print('LIPS smoothed', int((zx > 0.05).sum()), 'welded verts, max move mm %.2f' % (np.abs(sm).max() * 1000))
    # fold check: head faces whose front-view orientation flips; squash and stretch of the moved faces
    t = tri[mat == mn.index('EboraHead')]
    def front_area(C):
        a = C[t]; return (a[:, 1, 0] - a[:, 0, 0]) * (a[:, 2, 2] - a[:, 0, 2]) - (a[:, 2, 0] - a[:, 0, 0]) * (a[:, 1, 2] - a[:, 0, 2])
    fa0, fa1 = front_area(D['co']), front_area(co)
    facing = D['co'][t].mean(1)[:, 1] < 0.0; big = np.abs(fa0) > 1e-8
    flips = int((facing & big & (np.sign(fa0) != np.sign(fa1))).sum())
    def tri_area(C):
        a = C[t]; return 0.5 * np.linalg.norm(np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]), axis=1)
    ar = tri_area(co) / np.maximum(tri_area(D['co']), 1e-12); moved = np.abs(co[t] - D['co'][t]).max((1, 2)) > 1e-5
    print('FACE moved verts', int((np.abs(d).max(1) > 1e-5).sum()), 'max dx/dy/dz mm', np.round(np.abs(d).max(0) * 1000, 1).tolist(),
          'front flips', flips, 'area ratio of moved faces min/max', round(float(ar[moved].min()), 2), round(float(ar[moved].max()), 2))
    D['co'] = co
    np.savez(sys.argv[2], **D)
