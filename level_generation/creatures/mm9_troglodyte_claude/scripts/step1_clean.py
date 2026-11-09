"""Meshy body -> clean symmetric mesh at MM9 height. Smart Topology gave each arm as torso -> tube A -> forearm, plus a blind tube B from beside the cheek that ends at the elbow. MM9's shoulder is B's root.
So: tube A and B's blind tip go, the torso is capped and faired, B is bridged into the forearm by rings along a smooth curve (the elbow). Left half (x>0) mirrored.
glTF frame: +Z forward, +Y up, x>0 the figure's left. Writes work/body0.npz (co, tri) and work/spines.npz."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
from loadglb import *
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P, T, _ = load('meshy/smart_v1/model_urls_glb.glb'); P, T, _, _ = weld(P, T); nc, l = comps(len(P), T)
SP = {c: P[l == c].copy() for c in range(nc)}; SPT = {c: T[(l == c)[T[:, 0]]] for c in range(nc)}
T = T[(l == 0)[T[:, 0]]]
S = 1.24; lift = -0.594 - P[l == 0, 1].min() * S; P = P * S; P[:, 1] += lift
T = T[P[T].mean(1)[:, 0] > 0]
def boundary(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return u[c == 1]
b = boundary(T)
seam = np.unique(b[(np.abs(P[b[:, 0], 0]) < .03) & (np.abs(P[b[:, 1], 0]) < .03)])
P[seam, 0] = 0
def face_adj(idx):
    remap = -np.ones(len(T), int); remap[idx] = np.arange(len(idx)); ed = {}
    for f in idx:
        a, b_, c = T[f]
        for u, v in ((a, b_), (b_, c), (c, a)):
            ed.setdefault((min(u, v), max(u, v)), []).append(remap[f])
    r, c_ = [], []
    for v in ed.values():
        if len(v) == 2: r.append(v[0]); c_.append(v[1])
    return coo_matrix((np.ones(len(r)), (r, c_)), shape=(len(idx), len(idx)))
def ring_faces(pt, n, target):
    n = np.asarray(n, float); n = n / np.linalg.norm(n)
    d = (P - pt) @ n; s = d[T]
    idx = np.where((s.min(1) < 0) & (s.max(1) > 0))[0]
    k, lab = connected_components(face_adj(idx), directed=False)
    cen = P[T[idx]].mean(1)
    best = min(range(k), key=lambda c: np.linalg.norm(cen[lab == c].mean(0) - target))
    print('ring at', np.round(pt, 3), 'loops', k, 'chosen', (lab == best).sum(), 'centre', cen[lab == best].mean(0).round(3))
    return idx[lab == best]
E_ = np.array([.30, .16, -.21])                                  # elbow
AX_F = np.array([.04, -.25, .22]); AX_F /= np.linalg.norm(AX_F)    # forearm direction
wall_torso = ring_faces(np.array([.156, 0, 0]), (1, 0, 0), np.array([.156, .41, -.216]))
wall_fore = ring_faces(np.array([.312, .105, -.16]), AX_F, np.array([.312, .105, -.16]))
wall_b = ring_faces(np.array([.235, 0, 0]), (1, 0, 0), np.array([.235, .22, -.14]))
walls = np.r_[wall_torso, wall_fore, wall_b]
rest = np.setdiff1d(np.arange(len(T)), walls)
k, lab = connected_components(face_adj(rest), directed=False)
cen = P[T[rest]].mean(1)
seed = np.argmin(np.linalg.norm(cen - np.array([.2, .45, -.234]), axis=1))
sizes = np.bincount(lab); print('sizes', np.sort(sizes)[::-1][:10])
for c_ in np.argsort(-sizes): print(c_, sizes[c_], cen[lab == c_].mean(0).round(3))
tip = [c_ for c_ in range(k) if sizes[c_] < 600 and np.linalg.norm(cen[lab == c_].mean(0) - np.array([.26, .17, -.175])) < .05]
print('blind tip regions', tip)
spin = [c_ for c_ in range(k) if sizes[c_] < 120 and cen[lab == c_].mean(0)[1] < -.1]
print('spine patches', spin)
kill = rest[np.isin(lab, [lab[seed]] + tip + spin)]
print('regions', k, 'kill', len(kill), 'bbox', P[T[kill]].reshape(-1, 3).min(0).round(3), P[T[kill]].reshape(-1, 3).max(0).round(3))
keep = np.ones(len(T), bool); keep[kill] = False; keep[walls] = False
rogue = np.linalg.norm(P - np.array([.211, -.322, -.215]), axis=1) < 1e-2
keep[rogue[T].any(1)] = False
Lf = P[T]; Lm = np.max([np.linalg.norm(Lf[:, 0] - Lf[:, 1], axis=1), np.linalg.norm(Lf[:, 1] - Lf[:, 2], axis=1), np.linalg.norm(Lf[:, 2] - Lf[:, 0], axis=1)], axis=0)
keep[(Lm > .1) & (P[T].mean(1)[:, 1] < 0)] = False
print('rogue faces', int(rogue[T].any(1).sum()), 'long', int(((Lm > .1) & (P[T].mean(1)[:, 1] < 0)).sum()))
T = T[keep]
b = boundary(T)
b = b[~(np.isin(b[:, 0], seam) & np.isin(b[:, 1], seam))]
adj = {}
for u, v in b: adj.setdefault(u, []).append(v); adj.setdefault(v, []).append(u)
print('valence', max(len(v) for v in adj.values()))
seen = set(); loops = []
for s in adj:
    if s in seen: continue
    lp = [s]; seen.add(s); cur = s
    while True:
        nx = [v for v in adj[cur] if v not in seen]
        if not nx: break
        cur = nx[0]; seen.add(cur); lp.append(cur)
    loops.append(np.array(lp))
print('loops', [(len(l_), P[l_].mean(0).round(3).tolist()) for l_ in loops])
def pick(t): return min([l_ for l_ in loops if len(l_) >= 8], key=lambda l_: np.linalg.norm(P[l_].mean(0) - t))
LT, LF, LB = pick([.156, .41, -.216]), pick([.312, .105, -.16]), pick([.235, .22, -.14])
small = [l_ for l_ in loops if 3 <= len(l_) < 8]
def orient(lp):
    """so that an existing face runs lp[i] -> lp[i+1]"""
    a, b_ = lp[0], lp[1]
    for f in T:
        for i in range(3):
            if f[i] == a and f[(i + 1) % 3] == b_: return lp
    return lp[::-1]
LT, LF, LB = orient(LT), orient(LF), orient(LB)
new = [P]; nv = len(P); nt = [T]; free = []
# torso cap
m = len(LT); c = P[LT].mean(0); rings = [LT]; NR = 5
for k_ in range(1, NR):
    t = k_ / NR; q = P[LT] * (1 - t) + c * t
    ids = np.arange(nv, nv + m); nv += m; new.append(q); rings.append(ids); free += ids.tolist()
cid = nv; nv += 1; new.append(c[None]); free.append(cid)
for r0, r1 in zip(rings[:-1], rings[1:]):
    for i in range(m):
        j = (i + 1) % m
        nt.append(np.array([[r0[j], r0[i], r1[i]], [r0[j], r1[i], r1[j]]]))
r1 = rings[-1]; nt.append(np.array([[r1[(i + 1) % m], r1[i], cid] for i in range(m)]))
# bridge LB -> LF: a swept tube along a Bezier, rings counter-clockwise about the path, parallel transport; both mesh loops are zipped on in the same sense
ca, cb = P[LB].mean(0), P[LF].mean(0)
ax_b = ca - np.array([.14, .37, .02]); ax_b /= np.linalg.norm(ax_b)
def ccw(lp, axis, c):
    q = P[lp] - c; s_ = np.cross(q, np.roll(q, -1, 0)) @ axis
    return lp if s_.sum() > 0 else lp[::-1]
LBc, LFc = ccw(LB, ax_b, ca), ccw(LF, AX_F, cb)
ra_, rb_ = np.linalg.norm(P[LB] - ca, axis=1).mean(), np.linalg.norm(P[LF] - cb, axis=1).mean()
print('radii', ra_, rb_)
c1 = ca + ax_b * .09; c2 = cb - AX_F * .09
def bez(t): return (1 - t) ** 3 * ca + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t * t * c2 + t ** 3 * cb
def dbez(t):
    d = 3 * (1 - t) ** 2 * (c1 - ca) + 6 * (1 - t) * t * (c2 - c1) + 3 * t * t * (cb - c2); return d / np.linalg.norm(d)
M = 16; ts = np.linspace(.14, .86, 8)
u = np.cross(ax_b, [0, 0, 1.]); u /= np.linalg.norm(u)
ids = []; prev = ax_b
for t in ts:
    d = dbez(t); v_ = np.cross(prev, d); s_ = np.linalg.norm(v_)
    if s_ > 1e-9:
        ax = v_ / s_; ang = np.arctan2(s_, prev @ d); u = u * np.cos(ang) + np.cross(ax, u) * np.sin(ang) + ax * (ax @ u) * (1 - np.cos(ang))
    prev = d; u = u - d * (u @ d); u /= np.linalg.norm(u); w_ = np.cross(d, u)
    r = ra_ * (1 - t) + rb_ * t + .006 * np.sin(np.pi * t)
    th = np.linspace(0, 2 * np.pi, M, endpoint=False)
    q = bez(t) + r * (np.cos(th)[:, None] * u + np.sin(th)[:, None] * w_)
    i_ = np.arange(nv, nv + M); nv += M; new.append(q); ids.append(i_); free += i_.tolist()
for r0, r1 in zip(ids[:-1], ids[1:]):
    for i in range(M):
        j = (i + 1) % M
        nt.append(np.array([[r0[i], r0[j], r1[j]], [r0[i], r1[j], r1[i]]]))
def zip_ccw(A_, B_, Q):
    """A_ ring toward the path start, B_ toward the path end, both ccw about the path."""
    n, m_ = len(A_), len(B_)
    # start pair: closest in angle after removing the centres
    a0 = Q[A_] - Q[A_].mean(0); b0 = Q[B_] - Q[B_].mean(0)
    j0 = np.argmax(b0 @ a0[0]); i, j, ci, cj = 0, j0, 0, 0; out = []
    while ci < n or cj < m_:
        a, a2, b_, b2 = A_[i % n], A_[(i + 1) % n], B_[j % m_], B_[(j + 1) % m_]
        adv = ci < n and (cj >= m_ or ci / n <= cj / m_)
        if adv: out.append([a, a2, b_]); i += 1; ci += 1
        else: out.append([a, b2, b_]); j += 1; cj += 1
    return np.array(out)
Pall = np.vstack(new)
nt.append(zip_ccw(LBc, ids[0], Pall)); nt.append(zip_ccw(ids[-1], LFc, Pall))
P = np.vstack(new); T = np.vstack(nt)
print('verts', len(P), 'faces', len(T))
# shards on the palm
Lf = P[T]; Lm = np.max([np.linalg.norm(Lf[:, 0] - Lf[:, 1], axis=1), np.linalg.norm(Lf[:, 1] - Lf[:, 2], axis=1), np.linalg.norm(Lf[:, 2] - Lf[:, 0], axis=1)], axis=0)
Ar = np.linalg.norm(np.cross(Lf[:, 1] - Lf[:, 0], Lf[:, 2] - Lf[:, 0]), axis=1) / 2
sh = (np.linalg.norm(P[T].mean(1) - np.array([.33, -.11, -.04]), axis=1) < .07) & (Lm > .022) & (Ar / Lm ** 2 < .06)
print('palm shards', int(sh.sum())); T = T[~sh]
# holes: every open boundary except the seam gets a fan
b = boundary(T); b = b[~(np.abs(P[b[:, 0], 0]) < 1e-9) | ~(np.abs(P[b[:, 1], 0]) < 1e-9)]
n_ = len(P); lab_ = connected_components(coo_matrix((np.ones(len(b)), (b[:, 0], b[:, 1])), shape=(n_, n_)), directed=False)[1]
add = []; PP = [P]
fe = {}
for f in T:
    for i in range(3): fe[(f[i], f[(i + 1) % 3])] = 1
cc = np.unique(lab_[b[:, 0]])
for c__ in cc:
    es = b[lab_[b[:, 0]] == c__]; vs = np.unique(es); cid = n_ + len(PP) - 1; PP.append(P[vs].mean(0)[None])
    for u, v in es:
        add.append([v, u, cid] if (u, v) in fe else [u, v, cid])
    print('hole', len(es), P[vs].mean(0).round(3))
P = np.vstack(PP); T = np.vstack([T] + ([np.array(add)] if add else []))
free += [i for i in range(n_, len(P))]
e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); N = len(P)
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N, N)).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
mask = np.zeros(N, bool); mask[free] = True
near = mask.copy()
for _ in range(4): near = (A @ near.astype(float) > 0) | near
ids_ = np.where(near & (np.abs(P[:, 0]) > 1e-6))[0]
Q = P.copy()
for it in range(160):
    L = (A @ Q) / deg[:, None] - Q
    Bi = (A @ L) / deg[:, None] - L
    Q[ids_] += (0.5 * L[ids_] * mask[ids_, None]) * (it > 100) - 0.2 * Bi[ids_]
P = Q
e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); N = len(P)
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N, N)).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
box = (np.abs(P[:, 0] - .22) < .08) & (P[:, 1] > -.44) & (P[:, 1] < -.18) & (P[:, 2] < -.12) & (P[:, 2] > -.33)
pal = np.linalg.norm(P - np.array([.33, -.11, -.04]), axis=1) < .06
ids_ = np.where(box | pal)[0]
for it in range(24):
    L = (A @ P) / deg[:, None] - P
    P[ids_] += (.6 if it % 2 == 0 else -.53) * L[ids_]
used, inv = np.unique(T, return_inverse=True); co_h = P[used]; tri_h = inv.reshape(-1, 3)
keep_ = (np.abs(co_h[:, 0]) < 1e-9) * 1.0
hand_ = np.linalg.norm(co_h - np.array([.37, -.2, .02]), axis=1) < .24
foot_ = co_h[:, 1] < -.52
e_ = None
print('half', len(co_h), len(tri_h), 'seam', int(keep_.sum()))
torso_ = (co_h[:, 1] > -.05) & (co_h[:, 2] < .08)
head_ = co_h[:, 2] > .12
pr_ = np.maximum.reduce([keep_, hand_ * .55, foot_ * .3, torso_ * .55]); pr_[head_ & (keep_ == 0)] = 0
np.savez('work/body_half.npz', co=co_h, tri=tri_h, protect=pr_)
sp = []
for c_ in (2, 3, 4, 5, 6, 7):
    sp.append((SP[c_] * S + [0, lift, 0], SPT[c_]))
np.savez('work/spines.npz', **{f'co{i}': a for i, (a, b_) in enumerate(sp)}, **{f'tri{i}': np.unique(b_, return_inverse=True)[1].reshape(-1, 3) for i, (a, b_) in enumerate(sp)})
