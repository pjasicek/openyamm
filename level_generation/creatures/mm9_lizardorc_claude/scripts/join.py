"""Body + head + spines. The body is cut at the neck plane, its ring conformed to the head's ring by a decaying displacement (the throat fills out); the head's ring is zipped on with a strip in the head material.
Writes work/joined.npz: co, tri, mat (0 body, 1 head), part (0 body, 1 head skin, 3,4 teeth, 5 spines, 6 eyes), nb (body vertices), neckw, jawk, co_up (upload pose)."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
Db = np.load('work/body1.npz'); Hb = np.load('work/head1.npz')
P, T, SRC, LAB = Db['co'].astype(float), Db['tri'], Db['src'].astype(float), Db['label']
Q, Th, part_h, jk, Qo = Hb['co'].astype(float), Hb['tri'], Hb['part'], Hb['jawk'], Hb['co_open'].astype(float)
A_ = np.radians(25.8); n = np.array([0, -np.sin(A_), np.cos(A_)]); p0 = np.array([0, .352, -.055]); u = np.array([1., 0, 0]); v = np.cross(n, u)
def boundary(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1); uu, c = np.unique(e, axis=0, return_counts=True); return uu[c == 1]
def face_graph(T):
    ed = {}
    for i, f in enumerate(T):
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])): ed.setdefault((min(a, b), max(a, b)), []).append(i)
    r, c = [], []
    for w in ed.values():
        if len(w) == 2: r.append(w[0]); c.append(w[1])
    return coo_matrix((np.ones(len(r)), (r, c)), shape=(len(T), len(T)))
from clip import clip
d = (P - p0) @ n; cen_ = P[T].mean(1)
# only the torso/head tube is cut: the hands and legs in front of the plane stay
near = (np.abs(cen_[:, 0]) < .30) & (cen_[:, 1] > .08)
far = ~near
mask = near.astype(int)
Pf, Tf, exf, _ = clip(P, T[near], p0, n, extras=(SRC,))     # the piece cut off stays in the paint upload as an occluder
uf, invf = np.unique(Tf, return_inverse=True); e_ = exf[0][uf]
np.savez('work/cutoff.npz', co_up=e_ + [0, 0, .10], co=Pf[uf], tri=invf.reshape(-1, 3))
Pc, Tc, ex, rim = clip(P, T[near], p0, -n, extras=(SRC, LAB[:, None].astype(float)))
SRC2 = ex[0]; LAB2 = np.rint(ex[1][:, 0]).astype(int)
P = np.vstack([Pc]); T = np.vstack([Tc, T[far]]); SRC = SRC2; LAB = LAB2
# drop what is cut off (front pieces left by the box)
from scipy.sparse.csgraph import connected_components as cc
e = np.vstack([T[:, [0, 1]], T[:, [1, 2]]]); nc_, ll = cc(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(P), len(P))), directed=False)
sz = np.bincount(ll[T[:, 0]], minlength=nc_); main_ = sz.argmax(); print('pieces', np.sort(sz)[-5:]); T = T[ll[T[:, 0]] == main_]
used, inv = np.unique(T, return_inverse=True); P = P[used]; SRC = SRC[used]; LAB = LAB[used]; T = inv.reshape(-1, 3)
print('body', len(P), len(T))
b = boundary(T); Lb = np.unique(b); print('body ring verts', len(Lb))
# head ring
bh = boundary(Th[part_h[Th[:, 0]] == 1])
hv = np.unique(bh); dh = (Q[hv] - p0) @ n
Lh = hv[np.abs(dh) < .012]; print('head boundary', len(hv), 'near plane', len(Lh), 'd range', dh.min().round(3), dh.max().round(3))
C = 0.5 * (np.array([0, (Q[Lh] @ v).max(), 0]) + np.array([0, (Q[Lh] @ v).min(), 0]))
cv = .5 * ((Q[Lh] - p0) @ v).max() + .5 * ((Q[Lh] - p0) @ v).min(); cen2 = p0 + v * cv
def polar(X):
    q = X - cen2; x, y = q @ u, q @ v; return np.arctan2(y, x), np.hypot(x, y)
th, r = polar(Q[Lh]); o = np.argsort(th); Lh = Lh[o]; th, r = th[o], r[o]
# smooth the jagged ring radius, flatten on the plane
gr = np.linspace(-np.pi, np.pi, 180, endpoint=False)
rr = np.interp(gr, th, r, period=2 * np.pi)
for _ in range(12): rr = .25 * np.roll(rr, 1) + .5 * rr + .25 * np.roll(rr, -1)
# the ring meets half way: the head's rim tapers in, the body fills out (a body ring moved the whole way left a flange at the cheeks)
thb0, rb0 = polar(P[Lb]); o0 = np.argsort(thb0); rb_s = np.interp(gr, thb0[o0], rb0[o0], period=2 * np.pi)
for _ in range(6): rb_s = .25 * np.roll(rb_s, 1) + .5 * rb_s + .25 * np.roll(rb_s, -1)
rr = rr + .6 * np.minimum(rb_s - rr, 0)
for _ in range(6): rr = .25 * np.roll(rr, 1) + .5 * rr + .25 * np.roll(rr, -1)
print('ring radius head/body', np.round(rr[::30], 3), np.round(rb_s[::30], 3))
rs = lambda t: np.interp(t, gr, rr, period=2 * np.pi)
def on_ring(t): return cen2 + np.outer(rs(t) * np.cos(t), u) + np.outer(rs(t) * np.sin(t), v)
dQ = on_ring(th) - Q[Lh]
print('head ring moves max', np.linalg.norm(dQ, axis=1).max().round(3))
# head ring displacement decays into the head (mesh diffusion)
def diffuse(Pp, Tt, ids, disp, it, decay):
    e = np.vstack([Tt[:, [0, 1]], Tt[:, [1, 2]], Tt[:, [2, 0]]]); N = len(Pp)
    A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N, N)).tocsr(); A.data[:] = 1
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)[:, None]
    D = np.zeros((N, 3)); D[ids] = disp
    for _ in range(it):
        D = (A @ D) / deg * decay; D[ids] = disp
    return D
Dh = diffuse(Q, Th, Lh, dQ, 26, .955); Dh *= (jk[:, None] < .01) * (Q[:, 2:3] < .16); Dh[part_h != 1] = 0
Q = Q + Dh
# body ring onto the head ring, in order
thb, rb = polar(P[Lb]); o = np.argsort(thb); Lb = Lb[o]; thb = thb[o]
dB = on_ring(thb) - P[Lb]
print('body ring moves max', np.linalg.norm(dB, axis=1).max().round(3), 'mean', np.linalg.norm(dB, axis=1).mean().round(3))
Dbd = diffuse(P, T, Lb, dB, 45, .985)
arm = (LAB >= 1) & (LAB <= 3)
Dbd[arm] *= .25
P = P + Dbd
# zip strip in the head material: copies of the body ring + head ring, both ccw round +n
def ccw(lp, X):
    q = X[lp] - cen2; s_ = np.cross(q, np.roll(q, -1, 0)) @ n
    return lp if s_.sum() > 0 else lp[::-1]
nb = len(P)
Pall = np.vstack([P, Q]); tall = np.vstack([T, Th + nb])
Lb2 = ccw(Lb, Pall); Lh2 = ccw(Lh + nb, Pall)
copies = np.arange(len(Pall), len(Pall) + len(Lb2)); Pall = np.vstack([Pall, Pall[Lb2]])
# orientation: the head surface runs toward -n from... test by the first zip
def zip_(A, B, X):
    n1, n2 = len(A), len(B); a0 = X[A[0]] - cen2; j0 = int(np.argmax((X[B] - cen2) @ a0)); i, j, ci, cj = 0, j0, 0, 0; out = []
    while ci < n1 or cj < n2:
        a, a2, b_, b2 = A[i % n1], A[(i + 1) % n1], B[j % n2], B[(j + 1) % n2]
        if ci < n1 and (cj >= n2 or ci / n1 <= cj / n2): out.append([a, a2, b_]); i += 1; ci += 1
        else: out.append([a, b2, b_]); j += 1; cj += 1
    return np.array(out)
Zs = zip_(copies, Lh2, Pall)     # rings ccw about +n, body ring at the rear (start), head at the front (end)
print('zip', len(Zs))
nh = len(Q)
# calf spines (MM9: a few short spines at the back of each calf), small closed cones rooted in the skin
import mm9_joints, json
Fj = json.load(open('work/fit.json'))['tgt']; kn, an = np.array(Fj['kn']), np.array(Fj['an'])
SV, SF, SU = [], [], []; nv = len(Pall)
Ddir = np.array([.25, -.35, -.9]); Ddir /= np.linalg.norm(Ddir)
upP = SRC + [0, 0, .10]
for t, L in ((.28, .085), (.46, .10), (.64, .075)):
    a = kn + (an - kn) * t
    for sg in (1, -1):
        m_ = np.linalg.norm(P[:nb] * [sg, 1, 1] - a, axis=1) < .13
        idx = np.where(m_)[0]; i = idx[np.argmax((P[idx] * [sg, 1, 1] - a) @ Ddir)]
        base = P[i] - Ddir * [sg, 1, 1] * .012; d_ = Ddir * [sg, 1, 1]
        w = np.cross(d_, [1., 0, 0]); w /= np.linalg.norm(w); x_ = np.cross(d_, w)
        th_ = np.linspace(0, 2 * np.pi, 5, endpoint=False)
        r0 = base + .011 * (np.cos(th_)[:, None] * w + np.sin(th_)[:, None] * x_)
        r1 = base + d_ * L * .45 + .006 * (np.cos(th_)[:, None] * w + np.sin(th_)[:, None] * x_)
        V = np.vstack([r0, r1, (base + d_ * L)[None]])
        F = []
        for q in range(5):
            b_ = (q + 1) % 5; F += [[q, b_, 5 + b_], [q, 5 + b_, 5 + q], [5 + q, 5 + b_, 10]]
        F = np.array(F)
        if np.cross(V[1] - V[0], V[6] - V[0]) @ (V[0] - base) < 0: F = F[:, [0, 2, 1]]
        SV.append(V); SF.append(F + nv); nv += len(V); SU.append(V - P[i] + upP[i])
Pall = np.vstack([Pall] + SV)
co = Pall; tri = np.vstack([T, Th + nb, Zs] + SF)
ns = sum(len(x) for x in SV); nsf = sum(len(x) for x in SF)
mat = np.r_[np.zeros(len(T), int), np.ones(len(Th) + len(Zs), int), np.zeros(nsf, int)]
part = np.r_[np.zeros(nb, int), part_h, np.ones(len(copies), int), np.full(ns, 5)]
neckw = np.zeros(len(co)); jawk = np.r_[np.zeros(nb), jk, np.zeros(len(copies)), np.zeros(ns)]
db = (co[:nb] - p0) @ n
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
neckw[:nb] = (1 - ss(-db, .0, .11)) * np.maximum(LAB == 0, ss(db, -.05, -.005)) * (co[:nb, 1] > .18) * (np.abs(co[:nb, 0]) < .34)
# upload pose
from scipy.spatial import cKDTree
dd, m_ = cKDTree(Q[Lh]).query(Pall[copies])
up = np.vstack([SRC + [0, 0, .10], Qo, Qo[Lh[m_]]] + SU)
# fair the join: a soft band round the ring over both surfaces (body ring <-> its head copies are one edge)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]], np.c_[Lb2, copies]]); N_ = len(co)
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N_, N_)).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)[:, None]
dist = cKDTree(co[copies]).query(co)[0]
wt = np.exp(-(dist / .05) ** 2)[:, None]; wt[(part > 1)] = 0; wt[copies] = 0; wt[Lb2] = 0; wt[Lh2] = 0
co = co.copy()
for it in range(30):
    co += (.55 if it % 2 == 0 else -.5) * wt * ((A @ co) / deg - co)
co[copies] = co[Lb2]
print('joined', len(co), len(tri), 'mat', np.bincount(mat), 'open', len(boundary(tri)))
np.savez('work/joined.npz', co=co, tri=tri, mat=mat, matnames=np.array(['Trog', 'TrogHead']), part=part, neckw=neckw, jawk=jawk, co_up=up, nb=nb, nh=nh, ringcopy=copies, ringhead=Lh[m_] + nb, ringbody=Lb2, ringall=np.r_[Lb2, Lh2, copies], lab=LAB)
np.savez('work/body_only.npz', co=co[:nb], tri=T)
