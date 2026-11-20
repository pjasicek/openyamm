#!/usr/bin/env python3
"""Per-face labels of the installed PeasantM1d LOD0 (before/mm9_pm1d.glb, node PM1d; prims PM1d_C (body), PM1dHead_C
(head set + MPFB hands)), from the GLB alone: connected pieces (welded by position), dominant joint and the head region mask
(R = hair, sampled at each face's UV centroid). The creature has no linings (no see-through fix linings were built), so
lining/lined/pair/twin are empty and mpqem.py re-emits nothing.
Parts: 1 shirt/tunic shell (torso + sleeves, the biggest body piece), 5 breeches, 6 boots (Foot/Toe pieces), 8 boot cuffs
(Calf pieces), 9 small body pieces (belt/buckle, front laces, boot buckles), 0 MPFB hands (Hand/finger/forearm pieces of the
head set), 20 face shell (face, ears, scalp, neck: the head set's piece reaching lowest), 22 eyes/mouth pieces (head pieces
with little hair paint), 21 hair pieces (hair paint >= 0.5).
Writes work/glb_parts.npz (glb_parts.py format of the PeasantM2d project)."""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio, bglbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_pm1d.glb', 'PM1d')
PR = ['PM1d_C', 'PM1dHead_C']
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
d2, b2 = bglbio.read(HERE / 'before' / 'mm9_pm1d.glb')
M = {m['name']: m for m in d2['materials']}
def image(i):
    im = d2['images'][i]; v = d2['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b2[o:o + v['byteLength']]))
hmask = np.asarray(image(d2['textures'][M['PM1dHead_C']['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA'), np.float64) / 255
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
        big = max(comps, key=lambda c: size[c])
        for c in comps:
            m = fl == c; u, cnt = np.unique(dj[m], return_counts=True); top = jn[u[cnt.argmax()]]
            if c == big: p = 1
            elif size[c] <= 80: p = 9
            elif 'Thigh' in top or 'Pelvis' in top or 'Spine' in top: p = 5
            elif 'Foot' in top or 'Toe' in top: p = 6
            elif 'Calf' in top: p = 8
            else: p = 9
            part[m] = p
    else:
        lowest = min((c for c in comps if not handj[dj[fl == c]].mean() > 0.5), key=lambda c: P[np.unique(T[fl == c]), 1].min())
        for c in comps:
            m = fl == c
            if handj[dj[m]].mean() > 0.5: p = 0
            elif c == lowest: p = 20
            elif hairv[m].mean() >= 0.5: p = 21
            else: p = 22
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
