#!/usr/bin/env python3
"""Thin tips the Imp's LOD collapse would blunt, as protected points for build_lods.py (imp-reduce-20261104): every claw (body
mask G regions: the tip is the vertex farthest from the region's border), both horn tips (head no-region faces above the brows,
highest TIPS vertices per side) and the tail's spade tip (Tail4-weighted vertices farthest from the Tail4 joint).
All are kept exactly in LOD0. Usage: lod_tips.py <glb> -> work/lod_tips.npy (GLB coordinates)"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glbpack as G, bglbio  # noqa: E402
src = sys.argv[1]; TIPS = 3
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == 'Imp' and 'mesh' in n)
pr = {p['material']: p for p in bglbio.prims(d, bytes(b), node['mesh'])}
lp, hp = pr['Imp_A'], pr['ImpHead_A']
limbs = lp['POSITION'].astype(np.float64); head = hp['POSITION'].astype(np.float64)
Jl, Wl = lp['JOINTS_0'], lp['WEIGHTS_0'].astype(np.float64)
skin = d['skins'][node['skin']]; jn = [d['nodes'][j]['name'] for j in skin['joints']]
ibm = G.acc(d, bytes(b), skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
keep = []; ntip = 0
from PIL import Image  # noqa: E402
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
def _mask(base, P_, T_, UV_):
    mk = np.asarray(Image.open(HERE.parent / 'work' / f'tex_{base}_A.png').convert('RGB'), np.float32); H_, W_ = mk.shape[:2]
    uv = UV_[T_].mean(1); x = np.clip((uv[:, 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[:, 1] % 1) * H_, 0, H_ - 1).astype(int)
    return mk[y, x]
def _tips(P_, T_, sel):
    key = np.round(P_, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T_[sel]]
    n = wv.max() + 1; r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    inside = np.zeros(n, bool); inside[FT.ravel()] = True
    other = np.zeros(n, bool); other[wv[T_[~sel]].ravel()] = True
    rep = np.zeros(n, np.int64); rep[wv] = np.arange(len(wv))
    out = []
    for c in np.unique(lab[FT[:, 0]]):
        vs = np.flatnonzero(inside & (lab == c)); border = vs[other[vs]]
        if len(vs) < 4 or not len(border):
            continue
        base = P_[rep[border]].mean(0); out.append(P_[rep[vs[np.argmax(np.linalg.norm(P_[rep[vs]] - base, axis=1))]]])
    return out
cl = _mask('Imp', limbs, lp['T'], lp['TEXCOORD_0'].astype(np.float64))[:, 1] > 128
ct = _tips(limbs, lp['T'], cl); keep += [np.array(ct)]; ntip += len(ct); print('CLAW tips', len(ct))
hm = _mask('ImpHead', head, hp['T'], hp['TEXCOORD_0'].astype(np.float64)); hc = head[hp['T']].mean(1)
hn = (hm <= 128).all(1) & (hc[:, 1] > 1.09)
for sgn in (-1, 1):
    vs = np.unique(hp['T'][hn & (np.sign(hc[:, 0]) == sgn)])
    if len(vs):
        keep.append(head[vs[np.argsort(-head[vs, 1])[:TIPS]]]); ntip += TIPS; print('HORN tip', head[vs[np.argmax(head[vs, 1])]].round(3).tolist())
k4 = jn.index('Bip01 Tail4'); w4 = (Wl * (Jl == k4)).sum(1); s4 = np.flatnonzero(w4 > 0.5)
if len(s4):
    j4 = np.linalg.inv(ibm[k4])[:3, 3]; far = s4[np.argsort(-np.linalg.norm(limbs[s4] - j4, axis=1))[:TIPS]]
    keep.append(limbs[far]); ntip += TIPS; print('TAIL tip', limbs[far[0]].round(3).tolist())
pts = np.vstack(keep); np.save(HERE.parent / 'work' / 'lod_tips.npy', pts); print('TIPS', len(pts))
