"""LOD1 colour fidelity: points on every LOD1 triangle (barycentric grid) coloured through LOD1's UVs against the
closest facing LOD0 point coloured through LOD0's UVs, both on the shared base colour. Mean and p95 error in 8-bit
levels, and the share of points over 24 levels. Usage: texpass_lod1_check.py <glb> [...]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import floats, mesh_by_name, np, read_glb, source_faces  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
from transfer_textures import closest_on_triangles, image, sample  # noqa: E402

G = np.array([(i, j) for i in range(5) for j in range(5 - i)]) / 4.0
B = np.stack([1 - G.sum(1), G[:, 0], G[:, 1]], 1)
for path in sys.argv[1:]:
    doc, binary = read_glb(Path(path))
    base = image(doc, binary, doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'])

    def prim(name):
        p = doc['meshes'][mesh_by_name(doc, name)]['primitives'][0]
        return (floats(doc, binary, p['attributes']['POSITION']), floats(doc, binary, p['attributes']['TEXCOORD_0']),
                source_faces(doc, binary, p))

    p0, u0, f0 = prim('Body')
    p1, u1, f1 = prim('Body_LOD1')
    pts = np.einsum('kc,tcd->tkd', B, p1[f1]).reshape(-1, 3)
    uv1 = np.einsum('kc,tcd->tkd', B, u1[f1]).reshape(-1, 2)
    n = np.cross(p1[f1][:, 1] - p1[f1][:, 0], p1[f1][:, 2] - p1[f1][:, 0])
    n = np.repeat(n / np.linalg.norm(n, axis=1, keepdims=True), len(B), 0)
    n0 = np.cross(p0[f0][:, 1] - p0[f0][:, 0], p0[f0][:, 2] - p0[f0][:, 0])
    n0 /= np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-12)
    _, cand = cKDTree(p0[f0].mean(1)).query(pts, k=32)
    d, bary = closest_on_triangles(pts, p0[f0[cand, 0]], p0[f0[cand, 1]], p0[f0[cand, 2]])
    d = d + np.where((n0[cand] * n[:, None]).sum(-1) < -.2, 1e3, 0)
    pick = np.argmin(d, 1)
    rows = np.arange(len(pts))
    face, w = cand[rows, pick], bary[rows, pick]
    uv0 = (w[:, :, None] * u0[f0[face]]).sum(1)
    err = np.abs(sample(base, uv1) - sample(base, uv0)).max(1)
    print(f'{path}: {len(pts)} points, error mean {err.mean():.1f} p95 {np.percentile(err, 95):.1f}, '
          f'over 24 levels {(err > 24).mean():.1%}')
