#!/usr/bin/env python3
"""Survey of the installed Basilisk LOD0 (one primitive): connected components, dominant bone class per face, region-mask
classes, UV-seam vertices. Writes work/survey.npz (per GLB face: comp, comp_size, cls, mask rgb at centroid)."""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_basilisk.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Basilisk' and 'mesh' in n)
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
p = gb.prims(doc, b, node['mesh'])[0]
P, T, J, W, UV = p['POSITION'].astype(float), p['T'], p['JOINTS_0'], p['WEIGHTS_0'].astype(float), p['TEXCOORD_0']
nF = len(T)
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c] / 3)


def cls_of(n):
    if n in ('Xhead', 'Xeye', 'Xheadpiv'):
        return 'head'
    if n.startswith('Xjaw'):
        return 'jaw'
    if n.startswith('Xfin'):
        return 'frill'
    if n.startswith('Xneck'):
        return 'neck'
    if n.startswith('Xtail'):
        return 'tail'
    if 'fing' in n or 'thumb' in n:
        return 'toes'
    if any(s in n for s in ('wrist', 'arm', 'elbow', 'pivot', 'base')) and n not in ('Xrearbase', 'Xmidbase', 'Xjawbase'):
        return 'leg'
    if n in ('Xrearbase', 'Xrearbase01', 'Xmidbase', 'Xmidbase01'):
        return 'leg'
    return 'body'


bcls = np.array([cls_of(n) for n in joints])
dom = fw.argmax(1)
cls = bcls[dom]
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
ncomp, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
print('vertices GLB', len(P), 'welded', nW, 'faces', nF, 'components', ncomp)
for c in np.argsort(-cnt)[:60]:
    sel = fl == c
    print(f'  comp {c}: {cnt[c]} faces, classes {Counter(cls[sel]).most_common(3)}, '
          f'centroid {P[T[sel]].reshape(-1, 3).mean(0).round(3)}, extent {np.ptp(P[T[sel]].reshape(-1, 3), 0).round(3)}')
print('size histogram', Counter(cnt.tolist()).most_common(20))
print('faces per class', Counter(cls.tolist()).most_common())
mi = doc['materials'][0]['extras']['openyamm_region_mask']['index']
im = doc['images'][doc['textures'][mi]['source']]; v = doc['bufferViews'][im['bufferView']]
import io
mask = np.asarray(Image.open(io.BytesIO(b[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])).convert('RGB'))
H, Wd = mask.shape[:2]
uc = UV[T].mean(1); x = np.clip((uc[:, 0] % 1) * Wd, 0, Wd - 1).astype(int); y = np.clip((uc[:, 1] % 1) * H, 0, H - 1).astype(int)
mc = mask[y, x]
print('mask image', mask.shape, 'unique centroid colours', Counter(map(tuple, (mc // 64 * 64).tolist())).most_common(8))
seam = np.zeros(nW, int)
for t, g in zip(FT.ravel(), T.ravel()):
    pass
ncopies = np.bincount(wv)
print('welded vertices with >1 GLB copy', int((ncopies > 1).sum()), 'max copies', ncopies.max())
np.savez(HERE / 'work' / 'survey.npz', comp=fl, comp_size=cnt[fl], cls=cls, mask=mc, dom=dom)
print(doc['materials'][0]['extras']['openyamm_region_ramps'][0].keys() if doc['materials'][0]['extras'].get('openyamm_region_ramps') else '')
print(len(doc['materials'][0]['extras']['openyamm_region_ramps']), [r['range'] for r in doc['materials'][0]['extras']['openyamm_region_ramps']])
