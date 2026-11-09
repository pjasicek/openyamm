"""Inputs of compose.py on the uv_fine layout: work/texel_xyz2048.npy (rest-pose position per 2048 texel, from the
raster of resample_approved.py) and work/islands.npy (UV island id per LOD0 triangle, texture_quality.islands).
Usage: texel_maps.py"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texture_quality as TQ  # noqa: E402

W = HERE / 'work'
d = np.load(W / 'lod0_before.npz')
lay = np.load(W / 'uv_fine.npz')
r = np.load(W / 'approved_fine_raster2048.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
xyz = np.zeros(tri_id.shape + (3,), np.float32)
xyz[cov] = (d['pos'][d['tri'][tri_id[cov]]] * bary[cov][:, :, None]).sum(1)
np.save(W / 'texel_xyz2048.npy', xyz)
np.save(W / 'islands.npy', TQ.islands(lay['uv'], lay['xyz']))
print('WROTE texel_xyz2048.npy, islands.npy')
