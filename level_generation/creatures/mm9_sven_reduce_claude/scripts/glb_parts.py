#!/usr/bin/env python3
"""Per-face part labels of the installed LOD0 (before/<cfg.GLB>), from the GLB alone: connected pieces (welded by position),
dominant joint; part codes per piece from scripts/cfg.py (PeasantM1 reduce project's glb_parts.py, adapted). The model has no
linings and none are added (the user's open decision on see-through gaps), so lining/lined/pair/twin are empty and mpqem.py
re-emits nothing. Writes work/glb_parts.npz."""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio, bglbio  # noqa: E402
import cfg  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / cfg.GLB, cfg.NODE)
PR = cfg.PR
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
d2, b2 = bglbio.read(HERE / 'before' / cfg.GLB)
M = {m['name']: m for m in d2['materials']}
def image(i):
    im = d2['images'][i]; v = d2['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b2[o:o + v['byteLength']]))
HAIR_SHELL = True
hmask = np.zeros((4, 4, 4))  # PeasantM1: no head region mask (tier B has its own head image); hair is painted on the shell
handj = np.array([any(t in x for t in (' Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm')) for x in jn])
out = dict(mat=[], part=[], cen=[], joint=[], comp=[])
for k, name in enumerate(PR):
    P, T, J, W, UV = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W'], D[name]['UV']
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True); inv = inv.ravel(); TT = inv[T]; n = inv.max() + 1
    e = np.concatenate([TT[:, [0, 1]], TT[:, [1, 2]], TT[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[TT[:, 0]]
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dj = acc.argmax(1); part = np.zeros(len(T), int)
    uvc = UV[T].mean(1); hh, ww = hmask.shape[:2]
    hairv = hmask[np.clip((uvc[:, 1] % 1 * hh).astype(int), 0, hh - 1), np.clip((uvc[:, 0] % 1 * ww).astype(int), 0, ww - 1), 0]
    comps = np.unique(fl); size = {c: int((fl == c).sum()) for c in comps}
    if k == 0:
        for c in comps:
            part[fl == c] = cfg.BODY_PIECES.get(int(c), 9)
    else:
        for c in comps:
            m = fl == c
            if handj[dj[m]].mean() > 0.5: p = 0
            else: p = cfg.HEAD_PIECES.get(int(c), 22)
            part[m] = p
    for c in comps:
        m = fl == c; vs = P[np.unique(T[m])]
        print(f'{name} piece {c:3d} tris {size[c]:5d} part {part[m][0]:2d} hair {hairv[m].mean():.2f} lo {vs.min(0).round(3)} hi {vs.max(0).round(3)}')
    out['mat'] += [k] * len(T); out['part'].append(part); out['cen'].append(P[T].mean(1)); out['joint'].append(dj)
    out['comp'].append(fl + (0 if k == 0 else 1000))
res = {kk: (np.concatenate(v) if kk != 'mat' else np.array(v)) for kk, v in out.items()}
nf = len(res['mat'])
res.update(jnames=np.array(jn), lining=np.zeros(nf, int), lined=np.zeros(nf, bool), pair=-np.ones(nf, np.int64),
           unmatched=np.zeros(nf, bool), voff=np.cumsum([0] + [len(D[x]['P']) for x in PR]),
           foff=np.cumsum([0] + [len(D[x]['T']) for x in PR]))
res['twin'] = -np.ones(res['voff'][-1], np.int64); res['ambig'] = np.zeros(res['voff'][-1], bool)
for p in np.unique(res['part']):
    print('part', p, int((res['part'] == p).sum()))
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
