#!/usr/bin/env python3
"""The giant's mallet from MM9's own stations (GIANT.abc piece `mallet`, rigid on Xhammer; no Codex master for a weapon shape).
Frame: MM9's Xhammer local axes at our 0.3 scale: head along x (+-0.25), hexagonal section in (y, z) as MM9's six corners, handle along +y
through the head. The handle runs to y = HANDLE_END (MM9's ends at 1.095): MM9 slides the handle through the right fist up to 1.18 in the
standing clips, so ours is longer and ends in a pommel. Raised bands near both ends of the head (MM9's iron bands).
Writes work/mallet.npz: V (local), F, UV (1024 x 512 atlas: head sides left half, end caps and bands right top, handle right bottom),
and the bind matrix of Xhammer in Blender world (from the true-handed source). Args: <true glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
HANDLE_R, HANDLE_END = 0.027, 1.30
SPLIT = 0.33                     # the shaft's UV seam (lower island to here, upper from here), below every grip (MM9 slides the right fist down to
                                 # 0.7 in the swing, the left holds 0.41-0.61): a ring of vertices inside a fist reads as the shaft in the palm heel
HEX = [(-0.353, 0.100), (-0.191, 0.188), (-0.029, 0.100), (-0.029, -0.100), (-0.191, -0.188), (-0.353, -0.100)]   # (y, z), MM9's corners
X0, X1 = -0.25, 0.25
BANDS = [(-0.215, -0.175), (0.175, 0.215)]
V, F, UV = [], [], []
def add(p, uv): V.append(p); UV.append(uv); return len(V) - 1
def quad(a, b, c, d): F.append((a, b, c)); F.append((a, c, d))
def ring_at(x, grow, u0, u1, v):
    """hex ring at x, grown outward by grow; uv along the perimeter in [u0, u1] at height v"""
    pts = np.array(HEX, float); cen = pts.mean(0); d = pts - cen; d = d / np.linalg.norm(d, axis=1, keepdims=True)
    pts = pts + d * grow
    per = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.r_[pts, pts[:1]], axis=0), axis=1))]
    return [add((x, p[0], p[1]), (u0 + (u1 - u0) * per[k] / per[-1], v)) for k, p in enumerate(np.r_[pts, pts[:1]])]
def strip(r0, r1):
    for k in range(len(r0) - 1): quad(r0[k], r0[k + 1], r1[k + 1], r1[k])
# head sides: x stations with raised bands (grow 0.008)
G = 0.008
xs = [(X0, 0), (BANDS[0][0], 0), (BANDS[0][0], G), (BANDS[0][1], G), (BANDS[0][1], 0), (BANDS[1][0], 0), (BANDS[1][0], G), (BANDS[1][1], G), (BANDS[1][1], 0), (X1, 0)]
# the band steps are walls at one x: their rings get v 3 mm apart so the wall's UV has height (no degenerate texels)
VX = [x for x, g in xs]
for k in range(1, len(xs) - 1):
    if xs[k][0] == xs[k + 1][0]: VX[k] -= 0.003; VX[k + 1] += 0.003
rings = [ring_at(x, g, 0.0, 0.5, 0.02 + 0.96 * (vx - X0) / (X1 - X0)) for (x, g), vx in zip(xs, VX)]
for a, b in zip(rings[:-1], rings[1:]): strip(a, b)
# end caps: hex fans, UV in the right-top square
for x, sgn, uc in ((X0, -1, 0.625), (X1, 1, 0.875)):
    c = add((x, -0.191, 0.0), (uc, 0.75))
    ring = []
    for k, (y, z) in enumerate(HEX):
        ring.append(add((x, y, z), (uc + 0.11 * z / 0.188, 0.75 + 0.22 * (y + 0.191) / 0.188)))
    for k in range(6):
        a, b = ring[k], ring[(k + 1) % 6]
        F.append((c, b, a) if sgn > 0 else (c, a, b))
# handle: 10-sided, y from -0.40 to HANDLE_END, pommel knob; UV right-bottom: u around (0.5..1), v along (0..0.45)
N = 10
st = [(-0.40, HANDLE_R * 0.9), (-0.39, HANDLE_R), (SPLIT, HANDLE_R), (HANDLE_END - 0.05, HANDLE_R), (HANDLE_END - 0.035, HANDLE_R * 1.45), (HANDLE_END - 0.01, HANDLE_R * 1.45), (HANDLE_END, HANDLE_R * 0.8)]
hr = []
for y, r in st:
    v = 0.02 + 0.43 * (y + 0.40) / (HANDLE_END + 0.40)
    hr.append([add((r * np.cos(2 * np.pi * k / N), y, r * np.sin(2 * np.pi * k / N)), (0.5 + 0.5 * k / N, v)) for k in range(N + 1)])
for a, b in zip(hr[:-1], hr[1:]):
    for k in range(N): quad(a[k], b[k], b[k + 1], a[k + 1])
for (y, r), sgn, uc in ((st[0], -1, 0.56), (st[-1], 1, 0.62)):        # caps on their own small discs in UV (iron)
    c = add((0.0, y, 0.0), (uc, 0.475))
    ring = [add((r * np.cos(2 * np.pi * k / N), y, r * np.sin(2 * np.pi * k / N)), (uc + 0.02 * np.cos(2 * np.pi * k / N), 0.475 + 0.02 * np.sin(2 * np.pi * k / N))) for k in range(N + 1)]
    for k in range(N): F.append((c, ring[k], ring[k + 1]) if sgn > 0 else (c, ring[k + 1], ring[k]))
V = np.array(V); F = np.array(F); UV = np.array(UV)
# outward winding check per face against the part's centre (head and handle separately)
cen = V[F].mean(1); nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
ref = np.where((np.abs(cen[:, 0]) < 0.24)[:, None] & (cen[:, 1] < -0.02)[:, None] & (cen[:, 1] > -0.36)[:, None], np.c_[np.zeros(len(cen)), np.full(len(cen), -0.191), np.zeros(len(cen))], np.c_[np.zeros(len(cen)), cen[:, 1], np.zeros(len(cen))])
head = (cen[:, 1] > -0.36) & (cen[:, 1] < -0.02) & (np.abs(cen[:, 2]) > HANDLE_R * 1.6) | (np.abs(cen[:, 0]) > 0.04)
ref[head] = [0, -0.191, 0]
bad = (nrm * (cen - ref)).sum(1) < 0
F[bad] = F[bad][:, [0, 2, 1]]
# ---- isometric UV islands, per corner (UVc), packed by hand into one square at about the body's texel density. uv_atlas.py on this
# 240-triangle hard-surface mesh left 18-31 charts with 23-70 % of the surface on charts under 8 triangles; here the head's sides are
# unrolled into one strip with each end cap hinged onto it, the shaft is two strips cut at SPLIT, and its two end discs are small islands.
NR, NS, N1 = len(rings), len(st), N + 1
HB, CB = 0, 7 * NR                       # head rings (7 vertices each, the 7th repeats the first), then the two end caps (centre + 6)
SB = CB + 14; DB = SB + N1 * NS          # shaft rings, then the two shaft discs (centre + N1)
assert len(V) == DB + 2 * (1 + N1)
cen_h = np.array(HEX).mean(0); base_r = np.linalg.norm(np.array(HEX) - cen_h, axis=1)
# head strip: u = perimeter position (each ring centred), v = arc length along the (x, grow) profile
vr = np.r_[0, np.cumsum([np.hypot(xs[r + 1][0] - xs[r][0], xs[r + 1][1] - xs[r][1]) for r in range(NR - 1)])]
def strip2d(r, k):
    pts = V[HB + 7 * r: HB + 7 * r + 7, 1:]
    per = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    return np.array([per[k] - per[-1] / 2, vr[r]])
def cap2d(cb, r, kc):
    """the cap's hexagon hinged onto ring r's side kc, unfolded away from the strip"""
    hx = V[cb + 1: cb + 7, 1:]; c0 = V[cb, 1:]
    A, B = strip2d(r, kc), strip2d(r, kc + 1); a, b = hx[kc], hx[(kc + 1) % 6]
    e2 = (B - A) / np.linalg.norm(B - A); e3 = (b - a) / np.linalg.norm(b - a)
    out = None
    for refl in (1, -1):
        R = np.array([[e2[0], -e2[1]], [e2[1], e2[0]]]) @ np.diag([1, refl]) @ np.array([[e3[0], e3[1]], [-e3[1], e3[0]]])
        f = lambda p, R=R: A + R @ (p - a)
        cc = f(c0)
        if (r == 0 and cc[1] < 0) or (r == NR - 1 and cc[1] > vr[-1]): out = f
    return out
CAPS = {CB: (0, 0), CB + 7: (NR - 1, 5)}          # X0 cap on ring 0's first side (left end), X1 cap on the last ring's last side (right end)
def shaft2d(i, k, i0):
    r = st[i][1]; vs = np.r_[0, np.cumsum([np.hypot(st[j + 1][0] - st[j][0], st[j + 1][1] - st[j][1]) for j in range(NS - 1)])]
    return np.array([r * 2 * np.pi * (k / N - 0.5), vs[i] - vs[i0]])
isplit = [y for y, r in st].index(SPLIT)
isl = np.zeros(len(F), int); P2 = np.zeros((len(F), 3, 2)); capf = np.zeros(len(F), int)
for fi, f in enumerate(F):
    f = list(f)
    if max(f) < CB:                                    # head strip
        isl[fi] = 0; P2[fi] = [strip2d((v - HB) // 7, (v - HB) % 7) for v in f]
    elif max(f) < SB:                                  # end caps, onto the strip
        cb = CB if max(f) < CB + 7 else CB + 7; r, kc = CAPS[cb]; fmap = cap2d(cb, r, kc)
        isl[fi] = 0; capf[fi] = 1 if cb == CB else 2; P2[fi] = [fmap(V[v, 1:]) for v in f]
    elif max(f) < DB:                                  # shaft strips
        ii = [(v - SB) // N1 for v in f]; kk = [(v - SB) % N1 for v in f]
        lower = max(ii) <= isplit; isl[fi] = 1 if lower else 2; i0 = 0 if lower else isplit
        P2[fi] = [shaft2d(i, k, i0) for i, k in zip(ii, kk)]
    else:                                              # shaft discs
        d0 = DB if max(f) < DB + 1 + N1 else DB + 1 + N1; isl[fi] = 3 if d0 == DB else 4
        P2[fi] = [V[v, [0, 2]] for v in f]
# one orientation for every island. The head strip is an isometric unrolling, so its UV orientation is the true outward winding: the
# band walls facing the head's middle (x = +-0.175) came out of the centre-based check above wound inward; rewind them here
sa = lambda T: (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 2, 0] - T[:, 0, 0]) * (T[:, 1, 1] - T[:, 0, 1])
ref = np.sign(np.median(sa(P2[(isl == 0) & (capf == 0)])))
rw = np.where((isl == 0) & (np.sign(sa(P2)) != ref))[0]
F[rw] = F[rw][:, [0, 2, 1]]; P2[rw] = P2[rw][:, [0, 2, 1]]
print('MALLET rewound head faces', len(rw), 'at x', sorted(set(np.round(V[F[rw]].mean(1)[:, 0], 3).tolist())))
for k in range(1, 5):                                 # the discs and the strips may come out mirrored: flip them whole
    m_ = isl == k
    if np.mean(np.sign(sa(P2[m_])) == ref) < 0.5: P2[m_, :, 0] *= -1
    assert np.all(np.sign(sa(P2[m_])) == ref), f'island {k} folds'
# placement (metres): the upper shaft lying along the top over the head island, the lower shaft lying in the gap under the strip
# right of the X0 cap, the two discs stacked at the end of that gap
GAPM = 0.012
def bb(m_): q = P2[m_].reshape(-1, 2); return q.min(0), q.max(0)
lo, hi = bb(isl == 0); P2[isl == 0] -= lo; hw, hh = hi - lo
ys0 = -lo[1]; ys1 = ys0 + vr[-1]                                   # the strip's bottom and top edges
xc0, xc1 = bb(capf == 1)[1][0], bb(capf == 2)[0][0]
for k in (1, 2): P2[isl == k] = P2[isl == k][..., ::-1] * np.array([1, -1])          # a quarter turn: lying down
lo, hi = bb(isl == 2); assert hi[0] - lo[0] <= hw, ('upper shaft', hi - lo, hw)
P2[isl == 2] += np.array([0, hh + GAPM]) - lo; lh = hi[1] - lo[1]               # the upper shaft along the top, over the head island
lo, hi = bb(isl == 1); uw, uh = hi - lo                                            # the lower shaft in the gap under the strip
assert xc0 + GAPM + uw <= hw and uh <= ys0, ('lower shaft', uw, hw - xc0, uh, ys0)
P2[isl == 1] += np.array([xc0 + GAPM, (ys0 - uh) / 2]) - lo
y = GAPM
for k in (3, 4):
    lo, hi = bb(isl == k)
    P2[isl == k] += np.array([hw - (hi[0] - lo[0]) - GAPM / 2, y]) - lo; y += hi[1] - lo[1] + GAPM
    assert xc0 + GAPM + uw + GAPM / 2 <= hw - (hi[0] - lo[0]) - GAPM / 2, ('discs', xc0 + uw, hw)
W, H = hw, hh + GAPM + lh
TEX, MARG = 768, 4
SCALE = (TEX - 2 * MARG) / max(W, H)
UVc = (P2 * SCALE + MARG) / TEX
print('MALLET UV islands', [int((isl == k).sum()) for k in range(5)], 'layout m', np.round([W, H], 3), 'px per m', round(SCALE, 1))
print('MALLET verts', len(V), 'tris', len(F), 'flipped', int(bad.sum()))
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
X = m.world({})[names.index('Xhammer')]
B = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])         # glTF -> Blender
np.savez(str(Path(__file__).resolve().parents[1] / 'work' / 'mallet.npz'), V=V, F=F, UV=UV, M=B @ X, UVc=UVc)
