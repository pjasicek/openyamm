#!/usr/bin/env python3
"""Yanmir's staff from MM9's own staff (YANMIR.abc piece `staff`, rigid on Ystaff / Ystafftop / Ystaffbot; none of those moves
against Ystaff in any clip, so ours is one rigid part on Ystaff). No Codex master for a weapon shape.
Frame: MM9's Ystaff local axes at our 0.3 scale: the shaft along +y from the foot (y = -1.27) to the head.
MM9 (review/../references_acc/v2/mm9_staff_views.png): a thick square pole, 7.0-8.4 cm across at our scale, of mottled grey-brown
speckled wood or stone; on top a tulip cup of silver knotwork petals (tips at x = -0.205, 0, +0.203, y = 1.238, the side petals
starting wide at x = +-0.146, y = 1.026) round a green gem.
Ours (follow-up r5, the coordinator: "match MM9's thickness, material and head shape"): a round 16-sided pole r 0.034-0.038 with a
slight swelling, mapped in four lengths that each take the whole width of the pole tile (u along the pole, seamless left-right, so the
texel density along and around is about even); a silver collar; a cup of four broad knotwork petals curving out from the collar to
r 0.15 at the gem and closing back in to pointed tips at r 0.13-0.20 (the two side petals taller and wider, as MM9's), each a thin
slab with a rim, bound by a thin silver ring at the gem's height (a cage); an octahedral green gem in the cup; a silver ferrule. 2.2 cm up its own axis so the foot meets the floor.
UV atlas (1024 x 1024, textures/yan_acc_*): v 0.00-0.50 pole tile, v 0.50-0.75 engraved silver (collar, petals, ferrule),
v 0.75-1.00 left half the gem, right half ice (the crown's spikes).
Writes work/staff.npz: V (local), F, UV, KIND (0 pole, 1 silver, 2 gem per face), M (Ystaff bind in Blender world, true-handed source).
Args: <true glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

V, F, UV, K = [], [], [], []


def add(p, uv):
    V.append(tuple(float(x) for x in p)); UV.append(uv); return len(V) - 1


def tri(a, b, c, k):
    F.append((a, b, c)); K.append(k)


def ring(y, r, n, u0, u1, v):
    return [add((r * np.cos(2 * np.pi * i / n), y, r * np.sin(2 * np.pi * i / n)), (u0 + (u1 - u0) * i / n, v)) for i in range(n + 1)]


def ring_v(y, r, n, u, v0, v1):
    """a ring whose texture coordinate runs round it in v (the pole: u along the pole)"""
    return [add((r * np.cos(2 * np.pi * i / n), y, r * np.sin(2 * np.pi * i / n)), (u, v0 + (v1 - v0) * i / n)) for i in range(n + 1)]


def strip(r0, r1, k):
    for i in range(len(r0) - 1):
        tri(r0[i], r1[i], r1[i + 1], k); tri(r0[i], r1[i + 1], r0[i + 1], k)


def cap(rg, y, uv, k, up):
    c = add((float(np.mean([V[i][0] for i in rg])), y, float(np.mean([V[i][2] for i in rg]))), uv)
    for i in range(len(rg) - 1):
        if up: tri(rg[i], c, rg[i + 1], k)
        else: tri(rg[i], rg[i + 1], c, k)


N = 16
Y0, Y1 = -1.175, 0.845
SEG = 4                                   # four lengths, each the whole tile width (u 0..1), v round the pole 0.02..0.48
def radius(y):
    t = (y - Y0) / (Y1 - Y0)
    return 0.034 + 0.004 * t + 0.0018 * np.sin(t * 19.0) * (1 - 0.5 * t)
edges = np.linspace(Y0, Y1, SEG + 1)
for s in range(SEG):
    ys = np.linspace(edges[s], edges[s + 1], 5)
    rows = [ring_v(y, radius(y), N, (y - edges[s]) / (edges[s + 1] - edges[s]) * 0.98 + 0.01, 0.02, 0.48) for y in ys]
    for a, b in zip(rows[:-1], rows[1:]):
        strip(a, b, 0)
SV = lambda t: 0.52 + 0.21 * t


def lathe(profile, k=1, v0=0.0, v1=1.0):
    L = np.r_[0, np.cumsum([np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(profile[:-1], profile[1:])])]
    rs = [ring(y, r, N, 0.0, 2.0, SV(v0 + (v1 - v0) * L[i] / L[-1])) for i, (y, r) in enumerate(profile)]
    for a, b in zip(rs[:-1], rs[1:]):
        strip(a, b, k)
    return rs


fer = lathe([(-1.272, 0.005), (-1.250, 0.022), (-1.215, 0.036), (-1.185, 0.041), (-1.170, 0.041), (-1.160, 0.036)], 1, 0.0, 0.3)
col = lathe([(0.830, 0.037), (0.842, 0.046), (0.872, 0.047), (0.882, 0.042), (0.905, 0.042), (0.915, 0.050), (0.945, 0.060),
             (0.965, 0.064), (0.975, 0.040)], 1, 0.3, 1.0)
cap(col[-1], 0.977, (0.5, SV(1.0)), 1, True)


def tri_d(a, b, c, d, k):
    """a triangle wound so its normal faces direction d"""
    n = np.cross(np.array(V[b]) - np.array(V[a]), np.array(V[c]) - np.array(V[a]))
    if n @ d < 0: b, c = c, b
    tri(a, b, c, k)


def petal(phi, height, rmid, rtip, width):
    """a lancet petal: centre line from the collar (r 0.050, y 0.95) out to rmid at the gem's height and on to rtip at its pointed tip;
    broad at a third of its length, narrowing to the point, its edges curled in a little (a cup); two faces 1 cm apart and a rim"""
    S, T = 9, 5                           # LOD0 budget: the whole figure stays under 15k
    out = np.array((np.cos(phi), 0.0, np.sin(phi))); tg = np.array((-np.sin(phi), 0.0, np.cos(phi)))
    s = np.linspace(0, 1, S); t = np.linspace(-1, 1, T)
    rr = np.interp(s, [0, 0.3, 0.65, 1.0], [0.050, rmid, 0.5 * (rmid + rtip), rtip])
    yy = 0.95 + height * s
    ww = width * np.sin(np.pi * np.clip(s, 0.04, 1.0) ** 0.55) * (1 - 0.55 * s) + 0.016 * (1 - s)
    ww[-1] = 0.0
    grid = {}; nrm_ = {}
    for side, off in ((0, 0.005), (1, -0.005)):
        for i in range(S):
            for j in range(T):
                c = out * rr[i] + np.array((0, yy[i], 0))
                p = c + tg * ww[i] * t[j] - out * 0.018 * (t[j] ** 2) * np.sin(np.pi * s[i]) + out * off
                grid[(side, i, j)] = add(p, (0.03 + 0.94 * s[i], SV(0.05 + 0.9 * (t[j] + 1) / 2)))
    for i in range(S - 1):
        for j in range(T - 1):
            for side, sgn in ((0, 1.0), (1, -1.0)):
                a, b, c, d = (grid[(side, i, j)], grid[(side, i + 1, j)], grid[(side, i + 1, j + 1)], grid[(side, i, j + 1)])
                tri_d(a, b, c, out * sgn, 1); tri_d(a, c, d, out * sgn, 1)
    for i in range(S - 1):
        for j, sgn in ((0, -1.0), (T - 1, 1.0)):
            a, b, c, d = grid[(0, i, j)], grid[(0, i + 1, j)], grid[(1, i + 1, j)], grid[(1, i, j)]
            tri_d(a, b, c, tg * sgn, 1); tri_d(a, c, d, tg * sgn, 1)
    for j in range(T - 1):
        a, b, c, d = grid[(0, 0, j)], grid[(0, 0, j + 1)], grid[(1, 0, j + 1)], grid[(1, 0, j)]
        tri_d(a, b, c, np.array((0, -1.0, 0)), 1); tri_d(a, c, d, np.array((0, -1.0, 0)), 1)
    return out


P0 = len(F)
for phi, h, rm, rt, w in ((0.0, 0.29, 0.13, 0.205, 0.080), (np.pi, 0.29, 0.13, 0.205, 0.080), (np.pi / 2, 0.26, 0.11, 0.07, 0.070), (-np.pi / 2, 0.26, 0.11, 0.07, 0.070)):
    petal(phi, h, rm, rt, w)
# a thin silver ring binds the petals at the gem's height: the cup reads as a cage (MM9's knotwork lantern)
NR, NT, RB, RT, YB = 24, 5, 0.112, 0.007, 1.035
tor = [[add((np.cos(2 * np.pi * i / NR) * (RB + RT * np.cos(2 * np.pi * j / NT)), YB + RT * np.sin(2 * np.pi * j / NT),
              np.sin(2 * np.pi * i / NR) * (RB + RT * np.cos(2 * np.pi * j / NT))), (i / NR * 3.0, SV(0.2 + 0.6 * j / NT))) for j in range(NT)] for i in range(NR)]
for i in range(NR):
    for j in range(NT):
        a, b, c, d = tor[i][j], tor[(i + 1) % NR][j], tor[(i + 1) % NR][(j + 1) % NT], tor[i][(j + 1) % NT]
        ang = 2 * np.pi * (i + 0.5) / NR; th = 2 * np.pi * (j + 0.5) / NT
        dn = np.array((np.cos(ang) * np.cos(th), np.sin(th), np.sin(ang) * np.cos(th)))
        tri_d(a, b, c, dn, 1); tri_d(a, c, d, dn, 1)
P1 = len(F)
G = np.array((0.0, 1.060, 0.0)); gr, gh = 0.045, 0.065
gem0 = len(F)
gv = [add(tuple(G + d), uv) for d, uv in (((0, gh, 0), (0.25, 0.97)), ((0, -gh, 0), (0.25, 0.78)), ((gr, 0, 0), (0.05, 0.875)),
                                          ((0, 0, gr), (0.18, 0.875)), ((-gr, 0, 0), (0.32, 0.875)), ((0, 0, -gr), (0.45, 0.875)))]
for a, b in ((2, 3), (3, 4), (4, 5), (5, 2)):
    tri(gv[0], gv[b], gv[a], 2); tri(gv[1], gv[a], gv[b], 2)
V = np.array(V, float); F = np.array(F, int); UV = np.array(UV, float); K = np.array(K, int)
# winding: lathe pieces and the gem outward from their axis / centre; petal slabs outward from the slab's mid surface
cen = V[F].mean(1); nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
out = cen - np.c_[np.zeros(len(F)), cen[:, 1], np.zeros(len(F))]
out[gem0:] = cen[gem0:] - G
pet = np.zeros(len(F), bool); pet[P0:P1] = True
flip = (np.einsum('ij,ij->i', nrm, out) < 0) & ~pet
F[flip] = F[flip][:, ::-1]
V[:, 1] += 0.022                         # the foot meets the floor (MM9 plants it 2 cm under)
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]
W = m.world({})[names.index('Ystaff')]
C = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)     # glTF Y-up -> Blender Z-up
out_path = Path(__file__).resolve().parents[1] / 'work' / 'staff.npz'
np.savez(out_path, V=V, F=F, UV=UV, KIND=K, M=C @ W)
print('STAFF', len(V), 'verts', len(F), 'tris', 'kinds', np.bincount(K).tolist(), 'bbox', V.min(0).round(3).tolist(), V.max(0).round(3).tolist())
