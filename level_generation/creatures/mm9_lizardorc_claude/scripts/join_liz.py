"""Body + head. Body half mirrored, tube cut at the neck plane, rings conformed half way, head ring zipped on with a strip in head material.
Writes work/joined.npz: co, tri, mat (0 body, 1 head), part (0 body, 1 head skin, 3,4 teeth, 7 tongue, 8 + shell), nb, nh, jawk, co_up (upload pose: Meshy's), ringcopy, ringhead, ringbody, ringall, comp; work/cutoff.npz."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
from clip import clip
from loadglb import comps
import headfr as H
Db = np.load('work/half1.npz'); Hb = np.load('work/head1.npz')
Ph, Th0, cp, SRC0, LAB0 = Db['co'].astype(float), Db['tri'], Db['comp'], Db['src'].astype(float), Db['label']
# mirror the body half
on = np.where(np.abs(Ph[:, 0]) < 1e-9)[0]; Ph[on, 0] = 0
n_ = len(Ph); rem = np.arange(n_, 2 * n_); rem[on] = on
P = np.vstack([Ph, Ph * [-1, 1, 1]]); T = np.vstack([Th0, rem[Th0][:, [0, 2, 1]]])
SRC = np.vstack([SRC0, SRC0 * [-1, 1, 1]]); LAB = np.r_[LAB0, LAB0]; CP = np.r_[cp, cp]
used, inv = np.unique(T, return_inverse=True); P = P[used]; SRC = SRC[used]; LAB = LAB[used]; CP = CP[used]; T = inv.reshape(-1, 3)
main = np.bincount(cp).argmax()
Q, Th, part_h, jk, Qo = Hb['co'].astype(float), Hb['tri'], Hb['part'], Hb['jawk'], Hb['co_open'].astype(float)
p0, n = H.PLANE_P, H.PLANE_N; u = np.array([1., 0, 0]); v = np.cross(n, u)
def boundary(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1); uu, c = np.unique(e, axis=0, return_counts=True); return uu[c == 1]
d = (P - p0) @ n; cen_ = P[T].mean(1)
near = (CP[T[:, 0]] == main) & (np.abs(cen_[:, 0]) < .34) & (cen_[:, 1] > .35)
far = ~near
Pf, Tf, exf, _ = clip(P, T[near], p0, n, extras=(SRC,))
uf, invf = np.unique(Tf, return_inverse=True); np.savez('work/cutoff.npz', co_up=exf[0][uf], co=Pf[uf], tri=invf.reshape(-1, 3))
Pc, Tc, ex, rim = clip(P, T[near], p0, -n, extras=(SRC, LAB[:, None].astype(float), CP[:, None].astype(float)))
SRC = ex[0]; LAB = np.rint(ex[1][:, 0]).astype(int); CP = np.rint(ex[2][:, 0]).astype(int); P = Pc
T = np.vstack([Tc, T[far]])
used, inv = np.unique(T, return_inverse=True); P = P[used]; SRC = SRC[used]; LAB = LAB[used]; CP = CP[used]; T = inv.reshape(-1, 3)
print('body', len(P), len(T))
nc, cl = comps(len(P), T); szc = np.bincount(cl); print('comps', nc, np.sort(szc)[::-1][:6])
B = boundary(T); Bv = np.unique(B); onp = Bv[np.abs((P[Bv] - p0) @ n) < 1e-5]; print('body boundary', len(Bv), 'on the plane', len(onp))
def largest_loop(E, ids, X):
    ids_ = set(ids.tolist()); E = E[np.isin(E, ids).all(1)]
    r = {v: i for i, v in enumerate(ids)}; nc_ = len(ids)
    from scipy.sparse.csgraph import connected_components as cc
    G = coo_matrix((np.ones(len(E)), ([r[a] for a in E[:, 0]], [r[b] for b in E[:, 1]])), shape=(nc_, nc_)); k, lb = cc(G, directed=False)
    per = np.zeros(k); np.add.at(per, lb[[r[a] for a in E[:, 0]]], np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)); print('loops', np.round(np.sort(per)[::-1][:5], 2), [(np.round(X[ids[lb == q]].min(0), 2).tolist(), np.round(X[ids[lb == q]].max(0), 2).tolist(), int((lb == q).sum())) for q in np.argsort(-per)[:3]])
    return ids[lb == per.argmax()]
Lb = largest_loop(B, onp, P)
bh = boundary(Th[part_h[Th[:, 0]] == 1]); hv = np.unique(bh); dh = (Q[hv] - p0) @ n
Lh = largest_loop(bh, hv[np.abs(dh) < .012], Q); print('head boundary', len(hv), 'near plane', len(Lh), dh.min().round(3), dh.max().round(3))
# the throat is a tube inside the neck: its loop gets a dark cap
ids_ = hv[np.abs(dh) < .012]; Lt = np.setdiff1d(ids_, Lh)
cap_c = Q[Lt].mean(0)
cv = .5 * ((Q[Lh] - p0) @ v).max() + .5 * ((Q[Lh] - p0) @ v).min(); cen2 = p0 + v * cv
def polar(X):
    q = X - cen2; x, y = q @ u, q @ v; return np.arctan2(y, x), np.hypot(x, y)
th, r = polar(Q[Lh]); o = np.argsort(th); Lh = Lh[o]; th, r = th[o], r[o]
gr = np.linspace(-np.pi, np.pi, 180, endpoint=False)
rr = np.interp(gr, th, r, period=2 * np.pi)
for _ in range(12): rr = .25 * np.roll(rr, 1) + .5 * rr + .25 * np.roll(rr, -1)
thb0, rb0 = polar(P[Lb]); o0 = np.argsort(thb0); rb_s = np.interp(gr, thb0[o0], rb0[o0], period=2 * np.pi)
for _ in range(6): rb_s = .25 * np.roll(rb_s, 1) + .5 * rb_s + .25 * np.roll(rb_s, -1)
print('ring radius head/body', np.round(rr[::30], 3), np.round(rb_s[::30], 3))
# the ring is the head's: the torso comes in to the neck. A ring half way stretched head skin into a flat sheet
for _ in range(6): rr = .25 * np.roll(rr, 1) + .5 * rr + .25 * np.roll(rr, -1)
rs = lambda t: np.interp(t, gr, rr, period=2 * np.pi)
def on_ring(t): return cen2 + np.outer(rs(t) * np.cos(t), u) + np.outer(rs(t) * np.sin(t), v)
dQ = on_ring(th) - Q[Lh]; print('head ring moves max', np.linalg.norm(dQ, axis=1).max().round(3))
def diffuse(Pp, Tt, ids, disp, it, decay):
    e = np.vstack([Tt[:, [0, 1]], Tt[:, [1, 2]], Tt[:, [2, 0]]]); N = len(Pp)
    A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N, N)).tocsr(); A.data[:] = 1
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    D = np.zeros((N, 3)); D[ids] = disp
    for _ in range(it):
        D = ((A @ D).T / deg).T * decay; D[ids] = disp
    return D
Dh = diffuse(Q, Th[part_h[Th[:, 0]] == 1], Lh, dQ, 26, .955); Dh[part_h != 1] = 0; Dh *= (((Q - p0) @ n)[:, None] < .14)
Q = Q + Dh
thb, rb = polar(P[Lb]); o = np.argsort(thb); Lb = Lb[o]; thb = thb[o]
dB = on_ring(thb) - P[Lb]; print('body ring moves max', np.linalg.norm(dB, axis=1).max().round(3))
mt = CP[T[:, 0]] == main
Dbd = diffuse(P, T[mt], Lb, dB, 60, .985); Dbd[CP != main] = 0
P = P + Dbd
def ccw(lp, X):
    q = X[lp] - cen2; s_ = np.cross(q, np.roll(q, -1, 0)) @ n
    return lp if s_.sum() > 0 else lp[::-1]
nb = len(P)
Pall = np.vstack([P, Q]); tall = np.vstack([T, Th + nb])
Lb2 = ccw(Lb, Pall); Lh2 = ccw(Lh + nb, Pall)
copies = np.arange(len(Pall), len(Pall) + len(Lb2)); Pall = np.vstack([Pall, Pall[Lb2]])
def zip_(A, B, X):
    n1, n2 = len(A), len(B); a0 = X[A[0]] - cen2; j0 = int(np.argmax((X[B] - cen2) @ a0)); i, j, ci, cj = 0, j0, 0, 0; out = []
    while ci < n1 or cj < n2:
        a, a2, b_, b2 = A[i % n1], A[(i + 1) % n1], B[j % n2], B[(j + 1) % n2]
        if ci < n1 and (cj >= n2 or ci / n1 <= cj / n2): out.append([a, a2, b_]); i += 1; ci += 1
        else: out.append([a, b2, b_]); j += 1; cj += 1
    return np.array(out)
Zs = zip_(copies, Lh2, Pall)
# orientation of the strip against its neighbour
print('zip', len(Zs))
co = Pall; tri = np.vstack([T, Th + nb, Zs])
fn = np.cross(co[Zs[:, 1]] - co[Zs[:, 0]], co[Zs[:, 2]] - co[Zs[:, 0]]); out = (co[Zs].mean(1) - cen2)
if (fn * out).sum() < 0: Zs = Zs[:, [0, 2, 1]]; tri = np.vstack([T, Th + nb, Zs])
# cap: fan over the throat loop
et = bh[np.isin(bh, Lt).all(1)]; ci = len(co); co = np.vstack([co, cap_c[None]])
Cap = np.c_[et + nb, np.full(len(et), ci)]
tri = np.vstack([tri, Cap]); Zs = np.vstack([Zs, Cap])
mat = np.r_[np.zeros(len(T), int), np.ones(len(Th) + len(Zs), int)]
shell = 8 + (CP - CP.min()); 
pb = np.where(CP == main, 0, 8 + CP)
part = np.r_[pb, part_h, np.ones(len(copies), int), [1]]
jawk = np.r_[np.zeros(nb), jk, np.zeros(len(copies) + 1)]
dd, m_ = cKDTree(Q[Lh]).query(Pall[copies])
up = np.vstack([SRC, Qo, Qo[Lh[m_]], Qo[Lt].mean(0)[None]])
# chin: the neck plane cut small holes in the open-jawed tip (the clip ran before the jaw closed): fans over them, UVs in assemble.py
ch_e = bh[(np.abs(Q[bh[:, 0], 0]) < .05) & (Q[bh[:, 0], 2] > .3) & (Q[bh[:, 0], 1] < .66)]
from scipy.sparse.csgraph import connected_components as cc_
ncc, lcc = cc_(coo_matrix((np.ones(len(ch_e)), (ch_e[:, 0], ch_e[:, 1])), shape=(len(Q), len(Q))), directed=False)
chin = []; newc = []; newu = []
for k in np.unique(lcc[ch_e[:, 0]]):
    ee = ch_e[lcc[ch_e[:, 0]] == k]; vv = np.unique(ee); ci = len(co) + len(newc); newc.append(Q[vv].mean(0)); newu.append(Qo[vv].mean(0))
    # face orientation from the neighbouring triangle on each edge
    for a_, b_ in ee:
        f_ = Th[((Th == a_).any(1)) & ((Th == b_).any(1))][0]; i_ = list(f_).index(a_); nxt = f_[(i_ + 1) % 3]
        chin.append([b_ + nb, a_ + nb, ci] if nxt == b_ else [a_ + nb, b_ + nb, ci])
print('chin fans', len(newc), len(chin))
co = np.vstack([co, np.array(newc)]); part = np.r_[part, np.ones(len(newc), int)]; jawk = np.r_[jawk, np.ones(len(newc))]; up = np.vstack([up, np.array(newu)])
# fair the join: soft band round the ring (body ring and its head copies are one edge)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]], np.c_[Lb2, copies]]); N_ = len(co)
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N_, N_)).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)[:, None]
dist = cKDTree(co[copies]).query(co)[0]
wt = np.exp(-(dist / .04) ** 2)[:, None]; wt[(part > 1)] = 0; wt[copies] = 0; wt[Lb2] = 0; wt[Lh2] = 0
co = co.copy()
for it in range(30):
    co += (.55 if it % 2 == 0 else -.5) * wt * ((A @ co) / deg - co)
co[copies] = co[Lb2]
copies_all = copies
print('joined', len(co), len(tri), 'mat', np.bincount(mat), 'open', len(boundary(tri)))
np.savez('work/joined.npz', co=co, tri=tri, mat=mat, matnames=np.array(['Liz', 'LizHead']), part=part, jawk=jawk, co_up=up, nb=nb, nh=len(Q), ringcopy=copies, ringhead=Lh[m_] + nb, ringbody=Lb2, ringall=np.r_[Lb2, Lh2, copies], label=np.r_[LAB, np.zeros(len(co) - nb, int)], chin=np.array(chin))
mainf = T[CP[T[:, 0]] == main]
np.savez('work/body_only.npz', co=co[:nb], tri=T, main=(CP == main))
if 0: pass
