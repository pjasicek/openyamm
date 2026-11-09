"""Texture pass step 3: per-texel surface data of the new layout (texpass/uv_layout.npz) at the given sizes.

For every texel centre inside a new UV triangle: the LOD0 triangle, its bind-space glTF position and normal, the
installed (old) UV at that surface point (to carry the approved region mask and compare tones), and whether it is a
head-set chart. Writes texpass/raster_<size>.npz with HxW arrays (triangle -1 outside the charts).
Usage: texpass_raster.py <uv_layout.npz> <size> [<size> ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import BEFORE, TP, floats, lod0_arrays, mesh_by_name, np, read_glb  # noqa: E402
from transfer_textures import rasterize  # noqa: E402

layout = np.load(sys.argv[1])
corner_uv = layout['corner_uv'].copy()
corner_uv[..., 1] = 1.0 - corner_uv[..., 1]  # Blender v up -> image rows (glTF v down)
head_face = layout['head_face']
doc, binary = read_glb(BEFORE)
pos, old_uv, faces = lod0_arrays(doc, binary)
normals = floats(doc, binary, doc['meshes'][mesh_by_name(doc, 'Body')]['primitives'][0]['attributes']['NORMAL'])
for size in map(int, sys.argv[2:]):
    tri, x, y, bary = rasterize(corner_uv, size)
    out = {'triangle': np.full((size, size), -1, np.int32), 'pos': np.zeros((size, size, 3), np.float32),
           'normal': np.zeros((size, size, 3), np.float32), 'old_uv': np.zeros((size, size, 2), np.float32),
           'head': np.zeros((size, size), bool)}
    corners = faces[tri]
    out['triangle'][y, x] = tri
    out['pos'][y, x] = (bary[:, :, None] * pos[corners]).sum(1)
    n = (bary[:, :, None] * normals[corners]).sum(1)
    out['normal'][y, x] = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    out['old_uv'][y, x] = (bary[:, :, None] * old_uv[corners]).sum(1)
    out['head'][y, x] = head_face[tri]
    np.savez_compressed(TP / f'raster_{size}.npz', **out)
    print(f'raster {size}: {(out["triangle"] >= 0).mean():.1%} of texels covered, head {out["head"].mean():.1%}')
