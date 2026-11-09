#!/usr/bin/env python3
"""Small holes in the outer shell (see-through gate, 2026-11-02: a 9 cm slit down each side of the vest front, a gap at each side of the
apron top, specks at the mouth corners and the nose tip). assemble_pg.py's needle filter also dropped a few long thin faces of the vest edge,
and two needle faces at the nose tip went before the upload. Every boundary loop of the dress / skirt / head shell (positions welded) with
at most MAXV vertices is filled by a fan, wound against its neighbours; the new faces get their own vertices at the same positions, one UV
(a texel of the neighbouring face) and the neighbour's original index for the weights. New faces only: the paid paints stay valid.
Args: <in uv npz> <out uv npz> [maxv 5]"""
import sys, collections
import numpy as np
D = dict(np.load(sys.argv[1])); MAXV = int(sys.argv[3]) if len(sys.argv) > 3 else 5
co, tri, uv, orig, mat, comp = D['co'], D['tri'], D['uv'], D['orig'], D['mat'], D['comp']
pn = [str(x) for x in D['names']]
fsel = np.where(np.isin(comp[tri[:, 0]], [pn.index(x) for x in ('dress', 'skirt', 'head')]))[0]
P = np.round(co, 5); U, inv = np.unique(P, axis=0, return_inverse=True); inv = inv.ravel()
directed = collections.defaultdict(list)      # welded (a, b) -> (face, local corner) for every directed edge
for f in fsel:
    t = tri[f]
    for k in range(3): directed[(inv[t[k]], inv[t[(k + 1) % 3]])].append((f, k))
und = collections.Counter()
for (a, b) in directed: und[(min(a, b), max(a, b))] += len(directed[(a, b)])
bnd = [(a, b) for (a, b) in directed if und[(min(a, b), max(a, b))] == 1]
nxt = {}
for a, b in bnd: nxt.setdefault(b, []).append(a)       # the fill runs against the face's edge a->b: b->a
loops = []; used = set()
for a, b in bnd:
    if (a, b) in used: continue
    loop = [b, a]; used.add((a, b)); cur = a; ok = True
    while True:
        # follow: next boundary edge whose face edge is (c -> cur), i.e. fill edge cur -> c
        opts = [x for (x, y) in bnd if y == cur and (x, y) not in used]
        if not opts: ok = False; break
        c = opts[0]; used.add((c, cur))
        if c == loop[0]: break
        loop.append(c); cur = c
        if len(loop) > 200: ok = False; break
    if ok: loops.append(loop)
newc, newu, newo, newcomp, newt = [], [], [], [], []
n0 = len(co); nf = 0
for loop in loops:
    if len(loop) > MAXV: continue
    # a representative npz vertex per welded index (from a neighbouring face) for weights and the UV texel
    reps = []
    for w in loop:
        f, k = next(iter(directed[[e for e in directed if e[0] == w][0]]))
        reps.append(tri[f][k])
    u0 = uv[reps[0]]
    cen_ = U[loop].mean(0)
    if pn[comp[reps[0]]] == 'head' and not (abs(cen_[0]) < 0.03 and 0.60 < cen_[2] < 0.635):
        # other head holes (the nose tip, user review r16: a dark dot): the neighbour texel of median brightness, not a nostril shadow
        from PIL import Image as _Im
        import os as _os
        _p = 'textures/pg_head_g2_fix.png'
        if _os.path.exists(_p):
            _img = np.asarray(_Im.open(_p).convert('RGB'), np.float32); _S = _img.shape[0]
            _nb = np.where((comp == pn.index('head')) & (np.linalg.norm(co - cen_, axis=1) < 0.006))[0]
            if len(_nb):
                _px = np.clip((uv[_nb, 0] * _S).astype(int), 0, _S - 1); _py = np.clip(((1 - uv[_nb, 1]) * _S).astype(int), 0, _S - 1)
                _l = _img[_py, _px].mean(1); u0 = uv[_nb[np.argmin(np.abs(_l - np.median(_l)))]]
    elif pn[comp[reps[0]]] == 'head' and abs(cen_[0]) < 0.03 and 0.60 < cen_[2] < 0.65:
        # holes in the lip line (coordinator review r14: they showed as pale tooth-like specks, their point UV sat on a skin texel):
        # a dark lip texel near the slit
        # the darkest lip texel of the head paint near the slit (a shadow in the closed lips)
        import os as _os
        from PIL import Image as _Im
        _p = 'textures/pg_head_g2_fix.png'
        hv_ = np.where((comp == pn.index('head')) & (np.abs(co[:, 0]) < 0.012) & (np.abs(co[:, 2] - 0.6247) < 0.003) & (co[:, 1] < -0.10))[0]
        if len(hv_) and _os.path.exists(_p):
            _img = np.asarray(_Im.open(_p).convert('RGB'), np.float32); _S = _img.shape[0]
            _px = np.clip((uv[hv_, 0] * _S).astype(int), 0, _S - 1); _py = np.clip(((1 - uv[hv_, 1]) * _S).astype(int), 0, _S - 1)
            _rgb = _img[_py, _px]; _red = (_rgb[:, 0] > _rgb[:, 1] * 1.5)
            _cand = np.where(_red)[0] if _red.any() else np.arange(len(hv_))
            u0 = uv[hv_[_cand[np.argmin(_rgb[_cand].sum(1))]]]
    base = n0 + len(newc)
    for w, r in zip(loop, reps):
        newc.append(U[w]); newu.append(u0); newo.append(orig[r]); newcomp.append(comp[r])
    for i in range(1, len(loop) - 1):
        newt.append([base, base + i, base + i + 1]); nf += 1
    print('FILL', len(loop), 'verts at', np.round(U[loop].mean(0), 3).tolist())
if newt:
    D['co'] = np.vstack([co, np.array(newc)]); D['uv'] = np.vstack([uv, np.array(newu)]); D['orig'] = np.concatenate([orig, newo])
    D['comp'] = np.concatenate([comp, newcomp]); D['tri'] = np.vstack([tri, np.array(newt)]); D['mat'] = np.concatenate([mat, np.zeros(len(newt), mat.dtype)])
    # material by the part: head faces into the head set
    D['mat'][len(tri):] = [1 if pn[c] == 'head' else 0 for c in np.array(newcomp)[np.array(newt)[:, 0] - n0]]
    if 'inner' in D: D['inner'] = np.concatenate([D['inner'], np.zeros(len(newt), bool)])
np.savez(sys.argv[2], **D); print('HOLES filled faces', nf)
