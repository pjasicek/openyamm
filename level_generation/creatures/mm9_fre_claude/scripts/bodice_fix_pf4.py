#!/usr/bin/env python3
"""Job 8 (user review 2026-11-04, review/user_20261104/6-8.png): small light triangles on the chest front and at the apron belt, jagged
spikes at the bodice hem over the belt. Causes (review/diag/): F1's Meshy bodice has open holes where its lacing sat (eyelet holes beside
the placket, loops of 4-14 edges) and two beside the belt; the dress is hollow, so a hole shows the dress's back from inside, which a
one-sided viewer culls (background). F1's laced bust hid them under the lacing pieces; the plain F4 bodice (bust_pf4.py pressed the lacing)
uncovers them. The hem is F1's sawtooth peplum (spike tips 2.5 cm below their neighbours at each side); MM9's F4 bodice ends straight at
the belt. Mesh step after eyelid_pf4.py, on the final uv npz (positions of F1's parts unchanged elsewhere):
- every small hole of the main bodice (loop <= 16 edges, perimeter < 16 cm) is filled (ear clipping in the loop's plane, wound like
  its neighbours). The fill faces get their own UV rows, mapped by the affine 3D -> UV map of the largest bordering bodice face, so they
  show the cloth next to the hole (no new texels needed);
- the two pressed lacing chevrons (small separate pieces at the placket, z 0.21-0.28) are dropped: the bodice under them is closed;
- the hem at the sides: its notches come down to the tips' line (height only), so the edge runs straight; the skirt's and lining's
  sawtooth top edges under it come down to z 0.098 at the sides, so they stay under the bodice.
LOD0 stays <= 15,000 (fills added, chevrons dropped). Args: <uv npz in> <uv npz out>"""
import sys, collections
import numpy as np
U = dict(np.load(sys.argv[1], allow_pickle=True))
co, tri, uv, orig = U['co'].copy(), U['tri'], U['uv'], U['orig']
mat, comp, inner = U['mat'], U['comp'], U['inner']
names = [str(x) for x in U['names']]; kd = names.index('dress')
fd = np.where(comp[tri[:, 0]] == kd)[0]
T = orig[tri[fd]]                                   # asm vertex ids: UV seams merged
nv = orig.max() + 1
Pa = np.zeros((nv, 3)); Pa[orig] = co
# pieces of the dress by asm connectivity
par = np.arange(nv)
def fnd(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
for t in T:
    r = fnd(t[0]); par[fnd(t[1])] = r; par[fnd(t[2])] = r
pid = np.array([fnd(t[0]) for t in T]); cnt = collections.Counter(pid); main = cnt.most_common(1)[0][0]
drop = np.zeros(len(tri), bool)
rep = {}
# ---- the pressed lacing chevrons
for p, n in cnt.items():
    if p == main: continue
    vs = np.unique(T[pid == p]); c = Pa[vs].mean(0)
    if abs(c[0]) < 0.03 and c[1] < -0.10 and 0.20 < c[2] < 0.28:
        drop[fd[pid == p]] = True; rep.setdefault('chevrons', []).append((int(n), np.round(c, 3).tolist()))
# ---- boundary loops of the main piece (directed edges of its faces)
fm = fd[pid == main]; Tm = orig[tri[fm]]
de = np.vstack([Tm[:, [0, 1]], Tm[:, [1, 2]], Tm[:, [2, 0]]]); dface = np.r_[fm, fm, fm]
und = collections.Counter(map(tuple, np.sort(de, 1)))
bnd = [(int(a), int(b), int(f)) for (a, b), f in zip(de, dface) if und[tuple(sorted((a, b)))] == 1]
nxt = collections.defaultdict(list); efc = {}
for a, b, f in bnd: nxt[a].append(b); efc[(a, b)] = f
seen = set(); loops = []
for a, b, f in bnd:
    if (a, b) in seen: continue
    L = [a]; cur = (a, b); ok = True
    while cur not in seen:
        seen.add(cur); L.append(cur[1]); n = nxt[cur[1]]
        if len(n) != 1: ok = False; break
        cur = (cur[1], n[0])
    if ok and L[-1] == L[0]: loops.append(L[:-1])
def area_uv(f):
    u = uv[tri[f]]; return 0.5 * abs(np.cross(u[1] - u[0], u[2] - u[0]))
new_co, new_uv, new_orig, new_tri, new_mat = [], [], [], [], []
nbase = len(co)
fills = []
for L in loops:
    P = Pa[L]; per = np.linalg.norm(P - np.roll(P, -1, 0), axis=1).sum()
    if len(L) > 16 or per > 0.16: continue
    # face orientation: the faces have edges L[i] -> L[i+1]; the fill runs the other way
    nrm = np.zeros(3)
    for i in range(len(L)):
        f = efc[(L[i], L[(i + 1) % len(L)])]; t = co[tri[f]]; nrm += np.cross(t[1] - t[0], t[2] - t[0])
    nrm /= np.linalg.norm(nrm)
    e1 = np.cross(nrm, [0, 0, 1.0]) if abs(nrm[2]) < 0.9 else np.cross(nrm, [1.0, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(nrm, e1)
    R = L[::-1]; Q = np.c_[(Pa[R] - P.mean(0)) @ e1, (Pa[R] - P.mean(0)) @ e2]
    # ear clipping; output triangles keep R's winding, which (seen along nrm) is the neighbours' winding
    idx = list(range(len(R))); sgn = np.sign(0.5 * np.sum(Q[:, 0] * np.roll(Q[:, 1], -1) - np.roll(Q[:, 0], -1) * Q[:, 1]))
    out = []; guard = 0
    while len(idx) > 3 and guard < 500:
        guard += 1; done = False
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            cr = np.cross(Q[b] - Q[a], Q[c] - Q[b])
            if np.sign(cr) != sgn or abs(cr) < 1e-12: continue
            inside = False
            for o in idx:
                if o in (a, b, c): continue
                d1 = np.cross(Q[b] - Q[a], Q[o] - Q[a]); d2 = np.cross(Q[c] - Q[b], Q[o] - Q[b]); d3 = np.cross(Q[a] - Q[c], Q[o] - Q[c])
                if (np.sign(d1) == sgn) and (np.sign(d2) == sgn) and (np.sign(d3) == sgn): inside = True; break
            if inside: continue
            out.append((a, b, c)); idx.pop(k); done = True; break
        if not done:
            out.append((idx[0], idx[1], idx[2])); idx.pop(1)
    out.append(tuple(idx))
    # UV: affine map of the largest bordering face (3D in its plane -> UV)
    fb = max({efc[(L[i], L[(i + 1) % len(L)])] for i in range(len(L))}, key=area_uv)
    p0, p1, p2 = co[tri[fb]]; u0, u1, u2 = uv[tri[fb]]
    M3 = np.c_[p1 - p0, p2 - p0]; Mu = np.c_[u1 - u0, u2 - u0]
    rows = {}
    for v in R:
        bc = np.linalg.lstsq(M3, Pa[v] - p0, rcond=None)[0]
        rows[v] = nbase + len(new_co); new_co.append(co[orig == v][0]); new_uv.append(u0 + Mu @ bc); new_orig.append(v)
    for a, b, c in out:
        nt = [rows[R[a]], rows[R[b]], rows[R[c]]]
        new_tri.append(nt); new_mat.append(mat[fb])
    fills.append((len(L), round(per * 100, 1), np.round(P.mean(0), 3).tolist(), len(out)))
rep['holes_filled'] = fills
# ---- hem spikes: the bottom loop of the bodice. At the sides (|x| > 9 cm) F1's peplum is a sawtooth (tips 2.5 cm below the notches),
# and the skirt's top edge under it is the same sawtooth; lifting the tips (r33/r34) bared the skirt's notches. The notches come down
# instead (height only): every side hem vertex drops to the lowest hem height within two loop neighbours (smoothed), so the edge runs
# straight along the tips' line, as MM9's bodice edge does, and still covers the skirt's top. The front notch under the buckle and the
# back stay.
hem = [L for L in loops if len(L) > 20 and Pa[L][:, 2].mean() < 0.14]
lowered = []; cut = []
for L in hem:
    Q = Pa[L].copy(); z = Q[:, 2]; n = len(L)
    zmin = np.min([np.roll(z, k) for k in range(-2, 3)], axis=0)
    zs = np.mean([np.roll(zmin, k) for k in (-1, 0, 1)], axis=0)
    side = np.clip((np.abs(Q[:, 0]) - 0.075) / 0.03, 0, 1)        # eased in from the front panel (a hard cut left a needle at the corner)
    zn = z - side * np.maximum(z - zs, 0)
    mv = z - zn
    for v, q, d in zip(L, zn, mv):
        if d > 1e-4:
            co[orig == v, 2] = q; lowered.append(int(v))
    rep['hem_max_drop_mm'] = round(float(mv.max()) * 1000, 1)
rep['hem_lowered'] = len(lowered)
# a side tip carried by one face only lies flat on the new line once its neighbours come down: a horizontal needle sticking out at the
# hip (review/arms/r38 hemB); that face is dropped, the edge between its neighbours becomes the hem
deg = collections.Counter(Tm.ravel())
for L in hem:
    for v in L:
        if deg[v] == 1 and abs(Pa[v, 0]) > 0.09:
            f = [f_ for f_ in fm if v in orig[tri[f_]]]; drop[f] = True; cut.append(int(v))
rep['side_tips_cut'] = cut
# the skirt's (and its lining's) top edge under the peplum is the same sawtooth; at the sides its tips (to z 0.131) stand outside the
# peplum in motion (dark teeth below the bodice edge, review/arms/r36). Above SKTOP they come down to SKTOP (height only), eased in from
# the front panel like the hem.
SKTOP = 0.098
for part in ('skirt', 'lining'):
    kp = names.index(part); vv = np.unique(orig[tri[comp[tri[:, 0]] == kp]])
    w = np.clip((np.abs(Pa[vv, 0]) - 0.075) / 0.03, 0, 1); dz = np.maximum(Pa[vv, 2] - SKTOP, 0) * w
    for v, d in zip(vv[dz > 1e-4], dz[dz > 1e-4]):
        co[orig == v, 2] -= d
    rep[part + '_top_lowered'] = int((dz > 1e-4).sum()); rep[part + '_top_max_mm'] = round(float(dz.max()) * 1000, 1)
# ---- assemble
keep = ~drop
co2 = np.vstack([co, np.array(new_co).reshape(-1, 3)]); uv2 = np.vstack([uv, np.array(new_uv).reshape(-1, 2)])
orig2 = np.r_[orig, np.array(new_orig, int)]; comp2 = np.r_[comp, np.full(len(new_co), kd)]
tri2 = np.vstack([tri[keep], np.array(new_tri, int).reshape(-1, 3)])
mat2 = np.r_[mat[keep], np.array(new_mat, int)]; inner2 = np.r_[inner[keep], np.zeros(len(new_tri), bool)]
U.update(co=co2, uv=uv2, orig=orig2, comp=comp2, tri=tri2, mat=mat2, inner=inner2)
np.savez(sys.argv[2], **U)
print('BODICE', {k: v for k, v in rep.items()}, 'tris', len(tri), '->', len(tri2))
