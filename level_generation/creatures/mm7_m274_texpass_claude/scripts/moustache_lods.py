"""Which triangles of each LOD (and shadow mesh) belong to the moustache: a triangle is moustache when its centre and
corners lie on the LOD0 moustache surface (within TOL) and nearer to it than to the remaining LOD0 surface, matched by
surface position because LOD1-3 are decimated. Reports per mesh the count, and the open edges the removal would leave
near the mouth. Usage: moustache_lods.py <glb> [json out]"""
import json
import sys
import types
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
TOL = 0.0015


def surface_distance(points, P, F, tree, k=24):
    _, cand = tree.query(points, k=min(k, len(F)))
    d, _ = TT.closest_on_triangles(points, P[F[cand, 0]], P[F[cand, 1]], P[F[cand, 2]])
    return d.min(1)


def classify(glb_path):
    g = Glb(glb_path)
    doc = g.doc
    must0 = np.load(HERE / 'work' / 'nomoustache' / 'moustache_faces.npy')
    lod0 = doc['meshes'][0]
    pr0 = lod0['primitives'][0]
    P0 = g.accessor(pr0['attributes']['POSITION']).astype(np.float64)
    F0 = g.accessor(pr0['indices']).reshape(-1, 3).astype(np.int64)
    Fm, Ff = F0[must0], F0[~must0]
    tm, tf = cKDTree(P0[Fm].mean(1)), cKDTree(P0[Ff].mean(1))
    meshes = [0] + lod0['extras']['openyamm_lods'] + lod0['extras']['openyamm_shadow_lods']
    out = {}
    for mi in meshes:
        pr = doc['meshes'][mi]['primitives'][0]
        P = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
        F = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
        if mi == 0:
            sel = must0.copy()
        else:
            pts = np.concatenate([P[F].mean(1), P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]])
            dm = surface_distance(pts, P0, Fm, tm).reshape(4, -1)
            df = surface_distance(pts, P0, Ff, tf).reshape(4, -1)
            sel = (dm[0] < TOL) & (dm[0] < df[0]) & ((dm[1:] < df[1:] + 1e-4).sum(0) >= 2)
        # open edges near the mouth after removal (welded by position)
        _, weld = np.unique(P.round(6), axis=0, return_inverse=True)
        weld = weld.ravel()
        keep = weld[F[~sel]]
        e = Counter()
        for a, b, c in keep:
            for u, v in ((a, b), (b, c), (c, a)):
                e[(min(u, v), max(u, v))] += 1
        wpos = np.zeros((weld.max() + 1, 3))
        wpos[weld] = P
        open_near = [k for k, v in e.items() if v == 1 and abs(wpos[k[0], 0]) < 0.05
                     and 1.43 < wpos[k[0], 1] < 1.48 and wpos[k[0], 2] > 0.1]
        out[doc['meshes'][mi]['name']] = {'mesh': mi, 'triangles': int(len(F)), 'moustache': int(sel.sum()),
                                          'open_edges_near_mouth': len(open_near),
                                          'open_edge_points': [wpos[k[0]].round(4).tolist() for k in open_near][:12]}
        np.save(HERE / 'work' / 'nomoustache' / f'remove_mesh{mi}.npy', sel)
    return out


if __name__ == '__main__':
    res = classify(sys.argv[1])
    for k, v in res.items():
        print(k, {a: b for a, b in v.items() if a != 'open_edge_points'})
    if len(sys.argv) > 2:
        json.dump(res, open(sys.argv[2], 'w'), indent=1)
