"""LOD1 texture check per atlas primitive: area-weighted points on LOD1 triangles; colour through LOD1's UVs against
the colour of the nearest LOD0 surface point (same side, same primitive) through LOD0's UVs, both from the primitive's
base colour. Usage: tp_lod1_check.py <glb> [...]"""
import sys
import types

import numpy as np
from scipy.spatial import cKDTree

import tp_common as C
import texlib
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(C.CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

cfg = C.config()
for path in sys.argv[1:]:
    g = C.Glb(path)
    doc = g.doc
    mi = C.lod0_mesh_index(doc, cfg['node'])
    import os
    lod1 = doc['meshes'][mi]['extras']['openyamm_lods'][int(os.environ.get('TP_LOD', '1')) - 1]   # TP_LOD=2/3: far LODs sharing LOD0 images

    def prim(m, pi):
        pr = doc['meshes'][m]['primitives'][pi]
        return (g.accessor(pr['attributes']['POSITION']).astype(np.float64),
                g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64),
                g.accessor(pr['indices']).reshape(-1, 3), pr)
    for pi in cfg['atlas_prims']:
        p0, u0, f0, pr0 = prim(mi, pi)
        p1, u1, f1, _ = prim(lod1, pi)
        tex = C.material_maps(doc['materials'][pr0['material']])['basecolor']
        img = np.asarray(g.image(doc['textures'][tex]['source']).convert('RGB'), np.float32)
        rng = np.random.default_rng(0)
        a1 = C.tri_area3(p1[f1])
        N = 60000
        t = rng.choice(len(f1), N, p=a1 / a1.sum())
        b = rng.dirichlet((1, 1, 1), N)
        pt = (p1[f1[t]] * b[:, :, None]).sum(1)
        c1 = texlib.bilinear(img, (u1[f1[t]] * b[:, :, None]).sum(1))
        fn1 = np.cross(p1[f1[t, 1]] - p1[f1[t, 0]], p1[f1[t, 2]] - p1[f1[t, 0]])
        _, cand = cKDTree(p0[f0].mean(1)).query(pt, k=min(16, len(f0)))
        d, w = TT.closest_on_triangles(pt, p0[f0[cand, 0]], p0[f0[cand, 1]], p0[f0[cand, 2]])
        fn0 = np.cross(p0[f0[cand, 1]] - p0[f0[cand, 0]], p0[f0[cand, 2]] - p0[f0[cand, 0]])
        d = d + np.where((fn0 * fn1[:, None]).sum(-1) < 0, 1e3, 0)
        best = np.argmin(d, 1)
        rows = np.arange(N)
        c0 = texlib.bilinear(img, (u0[f0[cand[rows, best]]] * w[rows, best][:, :, None]).sum(1))
        err = np.abs(c1 - c0).mean(1)
        print(path.split('/')[-1], f'prim {pi}', 'LOD1 vs LOD0 colour error mean %.1f p95 %.1f p99 %.1f share>40 %.2f%%'
              % (err.mean(), np.percentile(err, 95), np.percentile(err, 99), 100 * (err > 40).mean()))
