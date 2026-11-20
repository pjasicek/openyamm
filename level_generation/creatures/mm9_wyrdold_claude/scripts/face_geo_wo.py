#!/usr/bin/env python3
"""Igrid's face geometry, finalised BEFORE any paint (brief 2026-11-02). Meshy modelled the mouth parted and pursed (a hole in the lower lip,
a slit open into a cavity) and left a loose lip shell over it (removed in assemble_wo.py). The mouth patch is rebuilt as a clean closed mouth:
1. delete the head faces whose centre lies in an x/z ellipse round the mouth (half axes MX x MZ about the slit line L) in front (y < YCUT),
   (the cavity behind stays inside the head, hidden); drop small islands left inside;
2. fill the hole: the hole's boundary loop + an even interior lattice (STEP), Delaunay in x/z, triangles outside the loop dropped;
3. depth: harmonic (membrane) interpolation of y from the boundary loop, plus subtle closed old lips: upper lip +UP mm 2 mm above L,
   lower lip +LO mm 2.8 mm below, a groove at the line, corners tucked and the slit lifted LIFT mm at the corners (a calm warm mouth).
Depth is a function of x^2 and the lattice is symmetric, so the mouth is symmetric. Positions only; run before UVs. Args: <asm npz> <out npz>"""
import sys, os, math
import numpy as np
from scipy.spatial import Delaunay
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from collections import defaultdict
IN, OUT = sys.argv[1:3]
E = lambda k, d: float(os.environ.get(k, d))
L, MX, MZ = E('L', '0.4855'), E('MX', '0.026'), E('MZ', '0.0155')
UP, LO, LIFT = E('UP', '0.7') / 1000, E('LO', '1.2') / 1000, E('LIFT', '0.8') / 1000
HALF, STEP = E('HALF', '0.021'), E('STEP', '0.0024')
D = dict(np.load(IN, allow_pickle=True)); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
H = names.index('head')
hv = np.where(comp == H)[0]; isH = np.isin(tri[:, 0], hv); ht = tri[isH]
u, inv = np.unique(ht.ravel(), return_inverse=True); hc = co[u].copy(); T = inv.reshape(-1, 3)
c = hc[T].mean(1); e = (c[:, 0] / MX) ** 2 + ((c[:, 2] - L) / MZ) ** 2
dele = (e < 1) & (c[:, 1] < float(os.environ.get('YCUT', '-0.26')))
T = T[~dele]
# drop small islands (face connectivity) left in the mouth region
ed = defaultdict(list)
for i, t in enumerate(T):
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): ed[(min(a, b), max(a, b))].append(i)
adj = defaultdict(list)
for fs in ed.values():
    if len(fs) == 2: adj[fs[0]].append(fs[1]); adj[fs[1]].append(fs[0])
lab = -np.ones(len(T), int); sizes = []
for f in range(len(T)):
    if lab[f] >= 0: continue
    st = [f]; lab[f] = len(sizes); n = 0
    while st:
        x = st.pop(); n += 1
        for y in adj[x]:
            if lab[y] < 0: lab[y] = lab[f]; st.append(y)
    sizes.append(n)
big = int(np.argmax(sizes)); cc = hc[T].mean(1); near = ((cc[:, 0] / MX) ** 2 + ((cc[:, 2] - L) / MZ) ** 2) < 2.5 ** 2
# every island but the face shell whose faces lie mostly round the mouth (the cavity behind the lips) goes
frac = np.array([near[lab == l].mean() for l in range(len(sizes))])
keepf = (lab == big) | (frac[lab] < 0.5)
print('MOUTH deleted', int(dele.sum()), 'faces; islands dropped', int((~keepf).sum()), 'components', sorted(sizes)[-4:])
T = T[keepf]
# boundary loop round the mouth
cnt = defaultdict(int); dire = {}
for t in T:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        cnt[(min(a, b), max(a, b))] += 1; dire[(a, b)] = 1
bd = [(a, b) for (a, b) in dire if cnt[(min(a, b), max(a, b))] == 1]
out = defaultdict(list)
for a, b in bd:
    p = (hc[a] + hc[b]) / 2
    if ((p[0] / MX) ** 2 + ((p[2] - L) / MZ) ** 2) < 2.0 ** 2: out[a].append(b)
used_e = set(); loops = []
for s0 in list(out):
    for b0 in out[s0]:
        if (s0, b0) in used_e: continue
        lp = [s0]; used_e.add((s0, b0)); x = b0
        while x != s0:
            lp.append(x); cand = [y for y in out.get(x, []) if (x, y) not in used_e]
            if not cand: break
            y = cand[0]; used_e.add((x, y)); x = y
        loops.append(lp)
loops = [l for l in loops if len(l) >= 8]; loop = min(loops, key=lambda l: hc[l, 1].mean())     # the front loop (the cavity island has its own loop behind)
print('LOOP mean y', [round(float(hc[l, 1].mean()), 4) for l in loops])
print('LOOPS', [len(l) for l in loops], 'bowtie vertices', sum(1 for v in out if len(out[v]) > 1))
B2 = hc[loop][:, [0, 2]]
# interior lattice (symmetric about x = 0), points inside the loop polygon and >= 0.6 STEP from it
nx = int(MX * 1.7 / STEP); xs = STEP * np.arange(-nx, nx + 1); nz = int(MZ * 1.7 / (STEP * 0.8)); zs = L + STEP * 0.8 * np.arange(-nz, nz + 1)
G = np.array([(x, z) for z in zs for x in xs])
def inside(P, poly):
    x, y = P[:, 0], P[:, 1]; res = np.zeros(len(P), bool); j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        cond = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi)
        res ^= cond; j = i
    return res
def segdist(P, poly):
    a = poly; b = np.roll(poly, -1, 0); best = np.full(len(P), 9.0)
    for i in range(len(a)):
        d = b[i] - a[i]; t = np.clip(((P - a[i]) @ d) / max(d @ d, 1e-15), 0, 1); q = a[i] + t[:, None] * d
        best = np.minimum(best, np.linalg.norm(P - q, axis=1))
    return best
G = G[inside(G, B2) & (segdist(G, B2) > STEP * 0.8)]
P2 = np.vstack([B2, G]); nb = len(B2)
tr = Delaunay(P2).simplices
cen = P2[tr].mean(1); tr = tr[inside(cen, B2)]
# orientation: counter-clockwise in (x, z) faces -y (front)
cr = (P2[tr[:, 1], 0] - P2[tr[:, 0], 0]) * (P2[tr[:, 2], 1] - P2[tr[:, 0], 1]) - (P2[tr[:, 1], 1] - P2[tr[:, 0], 1]) * (P2[tr[:, 2], 0] - P2[tr[:, 0], 0])
tr[cr < 0] = tr[cr < 0][:, ::-1]
# every loop edge must be a triangle edge (else the patch leaks)
te = set()
for t in tr:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): te.add((min(a, b), max(a, b)))
miss = sum(1 for i in range(nb) if (min(i, (i + 1) % nb), max(i, (i + 1) % nb)) not in te)
fix = []
for i in range(nb):
    a, b = i, (i + 1) % nb
    if (min(a, b), max(a, b)) in te: continue
    m = (P2[a] + P2[b]) / 2; cand = [j for j in range(nb, len(P2))]
    g_ = min(cand, key=lambda j: np.linalg.norm(P2[j] - m)); t = np.array([a, b, g_])
    cr_ = (P2[t[1], 0] - P2[t[0], 0]) * (P2[t[2], 1] - P2[t[0], 1]) - (P2[t[1], 1] - P2[t[0], 1]) * (P2[t[2], 0] - P2[t[0], 0])
    fix.append(t if cr_ > 0 else t[::-1])
if fix: tr = np.vstack([tr, np.array(fix)])
print('PATCH', len(G), 'new verts', len(tr), 'tris; loop edges missing', miss, 'fixed', len(fix))
# membrane depth from the loop, then the lips
n = len(P2); A = lil_matrix((n, n)); rhs = np.zeros(n)
nbrs = defaultdict(set)
for t in tr:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): nbrs[a].add(b); nbrs[b].add(a)
for i in range(n):
    if i < nb: A[i, i] = 1; rhs[i] = hc[loop[i], 1]
    else:
        A[i, i] = len(nbrs[i])
        for j in nbrs[i]: A[i, j] = -1
y = spsolve(A.tocsr(), rhs)
g = lambda x, s: np.exp(-(x / s) ** 2)
X = P2[nb:, 0]; Z = P2[nb:, 1] - L; uu = np.abs(X) / HALF; t_ = np.clip(1 - uu * uu, 0, 1)
lz = Z - LIFT * np.minimum(uu, 1) ** 2
d = UP * t_ ** 0.7 * g(lz - 0.0020, 0.0017) + LO * t_ ** 0.7 * g(lz + 0.0028, 0.0022) - 0.0005 * t_ * g(lz, 0.0006) - 0.0005 * g(uu - 1, 0.2) * g(lz, 0.003)
ph = (np.abs(X) < 0.004) & (Z > 0.004) & (Z < 0.011); d[ph] -= 0.0003 * (1 - np.abs(X[ph]) / 0.004) * np.sin(np.pi * (Z[ph] - 0.004) / 0.007)
dl = segdist(P2[nb:], B2); fade = np.clip(dl / (3 * STEP), 0, 1)
yn = y[nb:] - d * fade
newp = np.c_[X, yn, P2[nb:, 1]]
idx = np.r_[np.array(loop), len(hc) + np.arange(len(G))]
hc2 = np.vstack([hc, newp]); T2 = np.vstack([T, idx[tr]])
used, inv2 = np.unique(T2.ravel(), return_inverse=True); hc2 = hc2[used]; T2 = inv2.reshape(-1, 3)
# soften the slope break where the patch meets Meshy's face: depth-only smoothing in a band round the loop (both sides), front faces only
ee = np.unique(np.sort(np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]]), axis=1), axis=0)
r_ = np.sqrt((hc2[:, 0] / MX) ** 2 + ((hc2[:, 2] - L) / MZ) ** 2); band = (r_ > 0.8) & (r_ < 1.3) & (hc2[:, 1] < -0.26)
wb = np.clip(1 - np.abs(r_ - 1.05) / 0.25, 0, 1) * band
degb = np.zeros(len(hc2)); np.add.at(degb, ee[:, 0], 1); np.add.at(degb, ee[:, 1], 1)
for _ in range(int(os.environ.get('BAND_IT', '8'))):
    acc = np.zeros(len(hc2)); np.add.at(acc, ee[:, 0], hc2[ee[:, 1], 1]); np.add.at(acc, ee[:, 1], hc2[ee[:, 0], 1])
    hc2[:, 1] += 0.5 * wb * (acc / np.maximum(degb, 1) - hc2[:, 1])
def minang(Pp, t):
    a = Pp[t[:, 1]] - Pp[t[:, 0]]; b = Pp[t[:, 2]] - Pp[t[:, 0]]; c_ = Pp[t[:, 2]] - Pp[t[:, 1]]
    def ang(x, y_): return np.degrees(np.arccos(np.clip((x * y_).sum(1) / (np.linalg.norm(x, axis=1) * np.linalg.norm(y_, axis=1) + 1e-12), -1, 1)))
    return np.minimum(np.minimum(ang(a, b), ang(-a, c_)), ang(-b, -c_))
print('PATCH min angle deg', round(float(minang(np.c_[P2[:, 0], np.r_[hc[loop, 1], yn], P2[:, 1]], tr).min()), 1), 'lip max mm', round(float(d.max()) * 1000, 2),
      'membrane depth range', y[nb:].min().round(4), y[nb:].max().round(4))
keep_v = np.where(comp != H)[0]; mp = -np.ones(len(co), int); mp[keep_v] = np.arange(len(keep_v))
ot = tri[~isH]
D.update(co=np.vstack([co[keep_v], hc2]), tri=np.vstack([mp[ot], T2 + len(keep_v)]), comp=np.r_[comp[keep_v], np.full(len(hc2), H)])
# 4. Eyelids: Meshy's lids nearly closed over the eyeballs (a 3 mm slit, lid margins at about +9 and -5 deg): the lid skin round each ball
#    is rotated about the eye's horizontal axis like an opening lid, upper UPDEG up, lower LODEG down, full within 1.5 mm of the ball and
#    fading out by 9 mm (brow and cheek stay), fading toward the corners; every moved vertex stays 0.6 mm outside the ball.
UPDEG, LODEG = E('UPDEG', '12'), E('LODEG', '7')
co_ = D['co']; comp_ = D['comp']; EC = D['eye_c']; ER = float(D['eye_r']); moved = 0
for sx in (1, -1):
    c = EC * [sx, 1, 1]; q = co_ - c; dd = np.linalg.norm(q, axis=1)
    cand = (comp_ == H) & (dd < ER + 0.009) & (np.abs(dd - ER) > 0.0003) & (q[:, 1] < 0.003)
    phi = np.degrees(np.arctan2(q[:, 2], -q[:, 1])); th = np.arctan2(q[:, 0] * sx, -q[:, 1])
    w = np.clip((ER + 0.009 - dd) / 0.0075, 0, 1) * np.clip(np.cos(th) ** 2, 0, 1)
    up = np.clip((phi - 2) / 10, 0, 1); lo = np.clip((-2 - phi) / 10, 0, 1)
    ang = np.radians(UPDEG * up - LODEG * lo) * w
    i = np.where(cand & (np.abs(ang) > 1e-5))[0]
    f, u_ = -q[i, 1], q[i, 2]; ca, sa = np.cos(ang[i]), np.sin(ang[i]); f2 = f * ca - u_ * sa; u2 = f * sa + u_ * ca
    newp = c + np.c_[q[i, 0], -f2, u2]
    dn = np.linalg.norm(newp - c, axis=1); push = dn < ER + 0.0006
    newp[push] = c + (newp[push] - c) / dn[push, None] * (ER + 0.0006)
    co_[i] = newp; moved += len(i)
co_[(comp_ == H) & (np.abs(co_[:, 0]) < 1e-6), 0] = 0.0
D['co'] = co_; print('EYELIDS opened', moved, 'vertices, upper', UPDEG, 'lower', LODEG)
np.savez(OUT, **D); print('FACEGEO', len(D['co']), len(D['tri']))
