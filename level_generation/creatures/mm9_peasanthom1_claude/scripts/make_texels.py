#!/usr/bin/env python3
"""Texel maps (1K) of rest positions: body (UVMap, body faces) and head (HeadUV, head faces, with the part number).
Project folder. Writes v2/work/texel_body_1k.npz (xyz, cov) and v2/work/texel_head_1k.npz (xyz, cov, comp)."""
import sys
import numpy as np
sys.path.insert(0, 'scripts')
from texel_xyz import texel_xyz
b = np.load('v2/work/uv_UVMap.npz')
X, cov, fid = texel_xyz('v2/work/uv_UVMap.npz', 1024, (b['head'] == 0) & (b['hand'] == 0))
np.savez_compressed('v2/work/texel_body_1k.npz', xyz=X, cov=cov)
h = np.load('v2/work/uv_HeadUV.npz')
XH, covh, fidh = texel_xyz('v2/work/uv_HeadUV.npz', 1024, h['head'] == 1)
comp = np.where(fidh >= 0, h['comp'][np.maximum(fidh, 0)], -1)
np.savez_compressed('v2/work/texel_head_1k.npz', xyz=XH, cov=covh, comp=comp)
print('TEXELS body', int(cov.sum()), 'head', int(covh.sum()), 'parts', np.unique(comp[comp >= 0]).tolist())
