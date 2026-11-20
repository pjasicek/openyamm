#!/usr/bin/env python3
"""Hat seat check at bind: for the installed head-set vertices within HATR m of either hat (mm9_honkhat, mm9_elderhonkhat on
Bip01 Head), the distance to the candidate's head-set surface (densely sampled), and the signed clearance of the candidate's
surface to each hat (minimum hat-vertex distance, installed vs candidate). Usage: hat_seat.py <candidate glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; REPO = HERE.parents[2]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
HATR = 0.02
doc, b, nd, S = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM'); _, _, _, Cd = glbio.load(sys.argv[1], 'HonkM')
names = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
ibm = glbio.arr(doc, b, doc['skins'][nd['skin']]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
head = np.linalg.inv(ibm[names.index('Bip01 Head')])
k = 8; i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k; bw = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
def surf(D):
    return np.einsum('sk,fkc->fsc', bw, D['P'][D['T']]).reshape(-1, 3)
cs = cKDTree(surf(Cd['HonkMHead'])); ss = cKDTree(surf(S['HonkMHead']))
for f in ('mm9_honkhat.glb', 'mm9_elderhonkhat.glb'):
    hd, hb = glbio.read_glb(REPO / 'assets_source' / 'worlds' / 'mm9' / 'models' / f)
    hn = next(n for n in hd['nodes'] if n.get('name') == 'Hat' and 'mesh' in n)
    hv = np.concatenate([glbio.arr(hd, hb, p['attributes']['POSITION']).astype(float) for p in hd['meshes'][hn['mesh']]['primitives']])
    hv = (head @ np.c_[hv, np.ones(len(hv))].T).T[:, :3]
    hp = S['HonkMHead']['P']; near = hp[cKDTree(hv).query(hp)[0] < HATR]
    dev = cs.query(near)[0]
    gi = ss.query(hv)[0]; gc = cs.query(hv)[0]; band = gi < 0.02
    print(f'{f}: installed head vertices within {HATR} m of the hat {len(near)}, their distance to the candidate surface '
          f'max {dev.max() * 1000:.2f} mm p95 {np.percentile(dev, 95) * 1000:.2f} mm | hat vertices within 2 cm of the head: '
          f'{int(band.sum())}, head-surface distance installed min/median {gi[band].min() * 1000:.2f}/{np.median(gi[band]) * 1000:.2f} mm, '
          f'candidate {gc[band].min() * 1000:.2f}/{np.median(gc[band]) * 1000:.2f} mm, largest increase {(gc - gi)[band].max() * 1000:.2f} mm')
