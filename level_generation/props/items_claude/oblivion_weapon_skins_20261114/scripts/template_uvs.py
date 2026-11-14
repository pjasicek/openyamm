#!/usr/bin/env python3
"""work/<template>/uv_template.npy from layout_measure.glb: the new UV of every template triangle corner, in the
template's triangle order (glTF v down). prep.py writes it itself since the bow; this recovers it for layouts made
before. Faces are matched by their centroids, corners by position.

Usage: python3 template_uvs.py <template>"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
import glb_io

name = sys.argv[1]
work = os.path.join(PROJECT, 'work', name)
tdoc, tbin = glb_io.read(os.path.join(REPO, 'assets_dev', 'engine', 'view_model', f'{name}.glb'))
_, tprim = glb_io.mesh_primitive(tdoc)
tp = glb_io.accessor(tdoc, tbin, tprim['attributes']['POSITION']).astype(np.float64)
tt = glb_io.accessor(tdoc, tbin, tprim['indices']).astype(np.int64).reshape(-1, 3)
ldoc, lbin = glb_io.read(os.path.join(work, 'layout_measure.glb'))
_, lprim = glb_io.mesh_primitive(ldoc)
lp = glb_io.accessor(ldoc, lbin, lprim['attributes']['POSITION']).astype(np.float64)
luv = glb_io.accessor(ldoc, lbin, lprim['attributes']['TEXCOORD_0']).astype(np.float64)
lt = glb_io.accessor(ldoc, lbin, lprim['indices']).astype(np.int64).reshape(-1, 3)
assert len(lt) == len(tt), (len(lt), len(tt))
from scipy.spatial import cKDTree
tree = cKDTree(lp[lt].mean(1))
uv = np.zeros((len(tt), 3, 2))
for f, t in enumerate(tt):
    _, g = tree.query(tp[t].mean(0))
    for c in range(3):
        d = np.linalg.norm(lp[lt[g]] - tp[t[c]], axis=1)
        assert d.min() < 1e-3, (f, d.min())
        uv[f, c] = luv[lt[g][int(np.argmin(d))]]
np.save(os.path.join(work, 'uv_template.npy'), uv)
print('TEMPLATE_UVS', name, uv.shape, 'u', uv[..., 0].min().round(3), uv[..., 0].max().round(3))
