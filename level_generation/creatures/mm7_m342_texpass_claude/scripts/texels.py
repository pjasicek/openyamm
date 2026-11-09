"""Per-texel surface data of the texture-pass layout at 2048: triangle id, barycentrics, rest position, piece and the
head-set / leg flags of the triangle (from work/lod0_before.npz). Cached in work/texels2048.npz.
Usage (library): texels.load() -> dict"""
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
LAYOUT = HERE / 'work' / 'uv_cc4_fine.npz'


def load():
    cache = HERE / 'work' / 'texels2048.npz'
    if cache.exists():
        return dict(np.load(cache))
    r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
    tri_id, bary = r['tri_id'], r['bary']
    lay = np.load(LAYOUT)
    before = np.load(HERE / 'work' / 'lod0_before.npz')
    cov = tri_id >= 0
    t = np.maximum(tri_id, 0)
    pos = (lay['xyz'][t] * bary[..., None]).sum(-2).astype(np.float32)
    pos[~cov] = np.nan
    out = {'tri_id': tri_id, 'bary': bary, 'cov': cov, 'pos': pos,
           'piece': np.where(cov, before['piece'][t], -1).astype(np.int16),
           'head': cov & before['head_face'][t], 'leg': cov & before['leg_face'][t]}
    np.savez_compressed(cache, **out)
    return out
