"""LOD texture check: area-weighted points on each lower LOD of the body (texpass.json first layout mesh); colour
through the LOD's UVs and its own base colour against the colour of the nearest LOD0 surface point (same side)
through LOD0's UVs and base colour. Run on the installed and the pass GLB. Usage: lod_check.py <glb> [...]"""
import sys
import types

import numpy as np
from scipy.spatial import cKDTree

import tp
import texlib

sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(tp.CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

for path in sys.argv[1:]:
    g = tp.Glb(path)
    doc = g.doc
    body = tp.mesh_index(doc, tp.CFG['layout_meshes'][0])

    def prim(i):
        pr = doc['meshes'][i]['primitives'][0]
        img = np.asarray(g.image(tp.material_images(doc, pr['material'])['basecolor']).convert('RGB'), np.float32)
        return (g.accessor(pr['attributes']['POSITION']).astype(np.float64),
                g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64),
                g.accessor(pr['indices']).reshape(-1, 3), img)
    p0, u0, f0, img0 = prim(body)
    tree = cKDTree(p0[f0].mean(1))
    line = []
    for level, mi in enumerate(doc['meshes'][body].get('extras', {}).get('openyamm_lods', []), start=1):
        p1, u1, f1, img1 = prim(mi)
        rng = np.random.default_rng(0)
        a1 = np.linalg.norm(np.cross(p1[f1[:, 1]] - p1[f1[:, 0]], p1[f1[:, 2]] - p1[f1[:, 0]]), axis=1)
        N = 60000
        t = rng.choice(len(f1), N, p=a1 / a1.sum())
        b = rng.dirichlet((1, 1, 1), N)
        pt = (p1[f1[t]] * b[:, :, None]).sum(1)
        c1 = texlib.bilinear(img1, (u1[f1[t]] * b[:, :, None]).sum(1))
        fn1 = np.cross(p1[f1[t, 1]] - p1[f1[t, 0]], p1[f1[t, 2]] - p1[f1[t, 0]])
        _, cand = tree.query(pt, k=16)
        d, w = TT.closest_on_triangles(pt, p0[f0[cand, 0]], p0[f0[cand, 1]], p0[f0[cand, 2]])
        fn0 = np.cross(p0[f0[cand, 1]] - p0[f0[cand, 0]], p0[f0[cand, 2]] - p0[f0[cand, 0]])
        d = d + np.where((fn0 * fn1[:, None]).sum(-1) < 0, 1e3, 0)
        best = np.argmin(d, 1)
        rows = np.arange(N)
        c0 = texlib.bilinear(img0, (u0[f0[cand[rows, best]]] * w[rows, best][:, :, None]).sum(1))
        err = np.abs(c1 - c0).mean(1)
        line.append(f'LOD{level} mean {err.mean():.1f} p95 {np.percentile(err, 95):.1f} p99 {np.percentile(err, 99):.1f} '
                    f'>40 {100 * (err > 40).mean():.2f}%')
    print(path.split('/')[-1], ' | '.join(line))
