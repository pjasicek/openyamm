"""Vein mask of MM9's Ghoul skin in our atlas: each texel takes the nearest point of MM9's own bind surface (true-handed), reads the high-pass of GHOUL2 there. mask(pos, cov, skin2) -> HxW 0..1"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb


def mask(pos, cov, skin, plain):
    g = Glb('source/g2/ghoul2_true.glb'); pr = g.json['meshes'][0]['primitives'][0]
    P = g.accessor(pr['attributes']['POSITION']); UV = g.accessor(pr['attributes']['TEXCOORD_0'])
    T = g.accessor(pr['indices']).astype(int).reshape(-1, 3)
    rng = np.random.default_rng(1); pts = []; uvs = []
    for _ in range(90):
        r = rng.dirichlet((1, 1, 1), len(T))[:, :, None]
        pts.append((P[T] * r).sum(1)); uvs.append((UV[T] * r).sum(1))
    pts = np.concatenate(pts); uvs = np.concatenate(uvs)
    bl = np.c_[pts[:, 0], -pts[:, 2], pts[:, 1]]                 # glTF -> Blender axes
    q = pos[cov]; d, ix = cKDTree(bl).query(q, workers=4)
    dog = lambda im: ndimage.gaussian_filter(im.mean(2), 0.7) - ndimage.gaussian_filter(im.mean(2), 2.5)
    hp = dog(skin) - dog(plain)                                  # GHOUL3 is the same paint without the veins
    u, v = uvs[ix, 0] * 256 - 0.5, uvs[ix, 1] * 256 - 0.5
    val = ndimage.map_coordinates(hp, [v, u], order=1, mode='wrap')
    m = np.zeros(cov.shape, np.float32); m[cov] = np.clip((val - 0.025) / 0.05, 0, 1) * (d < 0.07)
    m = ndimage.gaussian_filter(m, 0.9)
    print('VEINS share %.3f' % float((m > 0.3).sum() / cov.sum()), 'dist p90 %.3f' % float(np.percentile(d, 90)))
    return m
