#!/usr/bin/env python3
"""UV parity of the Meshy return against the upload (both in upload space): every upload corner must find a return
corner at the same (scaled) position with the same UV. Prints matched / unmatched / changed."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent)); import glb_raster as G  # noqa: E402
P = Path(__file__).resolve().parents[1]


def corners(path):
    doc, b = G.read_glb(path); pos, uv = [], []
    for m in doc['meshes']:
        for p in m['primitives']:
            P_ = G.arr(doc, b, p['attributes']['POSITION']); U = G.arr(doc, b, p['attributes']['TEXCOORD_0'])
            I = G.arr(doc, b, p['indices']).ravel(); pos.append(P_[I]); uv.append(U[I])
    return np.concatenate(pos).astype(np.float64), np.concatenate(uv).astype(np.float64)


up_p, up_u = corners(P / 'work/body_upload.glb'); me_p, me_u = corners(P / 'meshy/body_texture_r1/model_urls_glb.glb')
s = np.ptp(up_p, 0).max() / np.ptp(me_p, 0).max()
me_p = (me_p - (me_p.max(0) + me_p.min(0)) / 2) * s + (up_p.max(0) + up_p.min(0)) / 2
key = np.hstack([me_p, me_u * 10]); tree = cKDTree(key)
d, _ = tree.query(np.hstack([up_p, up_u * 10]))
print('UV_PARITY corners', len(up_p), 'exact', int((d < 1e-4).sum()), 'off', int((d >= 1e-4).sum()), 'max', float(d.max()))
