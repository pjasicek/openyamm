"""LOD1 texture check: area-weighted points on LOD1 triangles; colour through LOD1's UVs against the colour of the
nearest LOD0 surface point (same side) through LOD0's UVs, both from the GLB's LOD0 base colour, before and after.
Usage: lod1_check.py <glb> [...]"""
import sys
import types
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
import texlib  # noqa: E402
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

for path in sys.argv[1:]:
    g = Glb(path)
    doc = g.doc
    meshes = doc['meshes']
    def prim(i):
        pr = meshes[i]['primitives'][0]
        return (g.accessor(pr['attributes']['POSITION']).astype(np.float64),
                g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64),
                g.accessor(pr['indices']).reshape(-1, 3))
    p0, u0, f0 = prim(0)
    p1, u1, f1 = prim(meshes[0]['extras']['openyamm_lods'][0])
    img = np.asarray(g.image(doc['textures'][doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB'), np.float32)
    rng = np.random.default_rng(0)
    a1 = np.linalg.norm(np.cross(p1[f1[:, 1]] - p1[f1[:, 0]], p1[f1[:, 2]] - p1[f1[:, 0]]), axis=1)
    N = 60000
    t = rng.choice(len(f1), N, p=a1 / a1.sum())
    b = rng.dirichlet((1, 1, 1), N)
    pt = (p1[f1[t]] * b[:, :, None]).sum(1)
    c1 = texlib.bilinear(img, (u1[f1[t]] * b[:, :, None]).sum(1))
    fn1 = np.cross(p1[f1[t, 1]] - p1[f1[t, 0]], p1[f1[t, 2]] - p1[f1[t, 0]])
    tree = cKDTree(p0[f0].mean(1))
    _, cand = tree.query(pt, k=16)
    d, w = TT.closest_on_triangles(pt, p0[f0[cand, 0]], p0[f0[cand, 1]], p0[f0[cand, 2]])
    fn0 = np.cross(p0[f0[cand, 1]] - p0[f0[cand, 0]], p0[f0[cand, 2]] - p0[f0[cand, 0]])
    d = d + np.where((fn0 * fn1[:, None]).sum(-1) < 0, 1e3, 0)
    best = np.argmin(d, 1)
    rows = np.arange(N)
    c0 = texlib.bilinear(img, (u0[f0[cand[rows, best]]] * w[rows, best][:, :, None]).sum(1))
    err = np.abs(c1 - c0).mean(1)
    print(Path(path).name, 'LOD1 vs LOD0 colour error mean %.1f p95 %.1f p99 %.1f share>40 %.2f%%'
          % (err.mean(), np.percentile(err, 95), np.percentile(err, 99), 100 * (err > 40).mean()))
