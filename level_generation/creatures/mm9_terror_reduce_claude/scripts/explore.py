#!/usr/bin/env python3
"""Terror LOD0 survey: connected pieces, cavity bag faces, region classes and dominant bones per face."""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_terror.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Terror' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W, UV = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float), pr['TEXCOORD_0'].astype(float)
print('verts', len(P), 'faces', len(T), 'bbox', P.min(0).round(3), P.max(0).round(3))
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
nc, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
for c in np.argsort(-cnt):
    f = fl == c; v = np.unique(T[f])
    print(f'piece {c}: faces {cnt[c]} centre {P[v].mean(0).round(3)} ext {np.ptp(P[v], 0).round(3)}')
bag = np.load(HERE.parent / 'mm9_terror_claude' / 'work' / 'uv_v3_bag.npz')
centre = bag['uv_new'].mean(1) * [1, -1] + [0, 1]
d, near = cKDTree(centre).query(UV[T].mean(1)); cav = d < 2e-4
print('cavity faces', int(cav.sum()), 'kinds', Counter(bag['kind'][near[cav]].tolist()))
m = np.asarray(Image.open(HERE / 'work' / 'tex_Terror_A.png').convert('RGB'), np.float32); H_, W_ = m.shape[:2]
uvc = UV[T].mean(1); x = np.clip((uvc[:, 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uvc[:, 1] % 1) * H_, 0, H_ - 1).astype(int)
ms = m[y, x]; g = 255 - ms.sum(1)
cls = np.argmax(np.c_[ms[:, 0], g, ms[:, 1], ms[:, 2]], 1)
print('region class (red, green, blue, bone) face counts', np.bincount(cls, minlength=4))
fw = np.zeros((len(T), len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(len(T)), J[T[:, k], c]), W[T[:, k], c])
dom = fw.argmax(1)
print('dominant bone face counts', sorted(((joints[i], int(n)) for i, n in Counter(dom.tolist()).items()), key=lambda x: -x[1]))
np.savez(HERE / 'work' / 'survey.npz', fl=fl, cav=cav, cls=cls, dom=dom)
