"""Puts the texture-pass layout and maps on the installed m322 elf GLB (MM7 mm7_m322).

Changes only UVs (and the vertex splits they need) and texture images; nodes, skin, clips, materials, variants, ramps
and every other attribute are carried over from the input GLB, so later layers on the installed file (head bob, Sprint
clips) survive. Steps:
1. LOD0 ('Elf') and its shadow copy: the layout's corner UVs; a vertex is split where the new layout has a
   seam. The input's LOD0 triangles and positions must equal work/lod0_before.npz (the mesh the layout was made on).
2. LOD1 and its shadow copy: each LOD1 triangle takes the LOD0 chart under its centre (nearest LOD0 triangle on the
   same side), and each of its corners the UV of the nearest point of that chart, so no LOD1 triangle spans a seam.
3. Images of the LOD0 material: base colour, metal/roughness, normal, region mask from <maps prefix>_{basecolor,
   metal_rough,normal,region_mask}.png.
4. LOD2/LOD3 keep their geometry and UVs (lod_repair_claude); their maps are transferred again from the new LOD0 with
   lod_repair_claude/scripts/transfer_textures.py at their installed sizes.

Usage: apply_layout.py <in glb> <layout npz> <maps prefix> <out glb>
"""
import io
import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
CREATURES = HERE.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(CREATURES / 'claude_shared'))
from glb import Glb, png  # noqa: E402
import texture_quality as TQ  # noqa: E402

# transfer_textures imports build_lods only for source_faces; build_lods needs pymeshlab for its own collapse, which
# is not used here.
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

NODE = 'Elf'


def split_vertices(corner_vid, corner_uv):
    """(T,3) vertex ids and (T,3,2) UVs -> source vertex per new vertex, new UV per new vertex, new indices."""
    key = np.concatenate([corner_vid.reshape(-1, 1).astype(np.float64), np.round(corner_uv.reshape(-1, 2), 7)], 1)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inverse = inverse.ravel()
    order = np.argsort(first)                 # keep the old vertex order as far as possible
    rank = np.empty_like(order)
    rank[order] = np.arange(len(order))
    src = corner_vid.reshape(-1)[first[order]]
    uv = corner_uv.reshape(-1, 2)[first[order]]
    return src, uv, rank[inverse].reshape(-1, 3)


def closest_on_triangles(points, a, b, c):
    """Closest points of triangles (N,K,3) to points (N,3): distance (N,K), barycentrics (N,K,3)."""
    return TT.closest_on_triangles(points, a, b, c)


def lod1_uvs(p0, f0, uv0_tri, chart, p1, f1, n1):
    """Corner UVs of LOD1 triangles from the LOD0 chart under each triangle's centre."""
    n0f = np.cross(p0[f0[:, 1]] - p0[f0[:, 0]], p0[f0[:, 2]] - p0[f0[:, 0]])
    n0f /= np.maximum(np.linalg.norm(n0f, axis=1, keepdims=True), 1e-12)
    tree = cKDTree(p0[f0].mean(1))
    centre = p1[f1].mean(1)
    fn = np.cross(p1[f1[:, 1]] - p1[f1[:, 0]], p1[f1[:, 2]] - p1[f1[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    K = 32
    _, cand = tree.query(centre, k=K)
    dist, _ = closest_on_triangles(centre, p0[f0[cand, 0]], p0[f0[cand, 1]], p0[f0[cand, 2]])
    cost = dist + np.where((n0f[cand] * fn[:, None]).sum(-1) < 0.0, 1e3, 0.0)
    host = cand[np.arange(len(f1)), np.argmin(cost, 1)]
    tri_chart = chart[host]
    out = np.zeros((len(f1), 3, 2))
    worst = 0.0
    by_chart = {}
    for c in np.unique(tri_chart):
        faces = np.nonzero(chart == c)[0]
        by_chart[c] = (faces, cKDTree(p0[f0[faces]].mean(1)))
    for t in range(len(f1)):
        faces, ctree = by_chart[tri_chart[t]]
        k = min(16, len(faces))
        _, local = ctree.query(p1[f1[t]], k=k)
        local = np.asarray(local).reshape(3, -1)
        cand_f = faces[local]                                        # (3, k)
        d, w = closest_on_triangles(p1[f1[t]], p0[f0[cand_f, 0]], p0[f0[cand_f, 1]], p0[f0[cand_f, 2]])
        best = np.argmin(d, 1)
        worst = max(worst, float(d[np.arange(3), best].max()))
        out[t] = (w[np.arange(3), best][:, :, None] * uv0_tri[cand_f[np.arange(3), best]]).sum(1)
    return out, worst


def main():
    src, layout_path, maps_prefix, dst = sys.argv[1:5]
    g = Glb(src)
    doc = g.doc
    node = next(n for n in doc['nodes'] if n.get('name') == NODE and 'mesh' in n)
    lod0 = doc['meshes'][node['mesh']]
    lods = lod0['extras']['openyamm_lods']
    shadows = lod0['extras']['openyamm_shadow_lods']
    before = np.load(HERE / 'work' / 'lod0_before.npz')
    layout = np.load(layout_path)
    pr0 = lod0['primitives'][0]
    p0 = g.accessor(pr0['attributes']['POSITION']).astype(np.float64)
    f0 = g.accessor(pr0['indices']).reshape(-1, 3).astype(np.int64)
    assert (f0 == before['tri']).all() and np.allclose(p0, before['pos'], atol=1e-6), \
        'LOD0 differs from the mesh the layout was made on'
    assert (layout['tri'] == f0).all()
    uv0_tri = layout['uv']
    chart = TQ.islands(uv0_tri, p0[f0])

    def rebuild(mesh_index, corner_uv):
        pr = doc['meshes'][mesh_index]['primitives'][0]
        faces = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
        srcv, uv, idx = split_vertices(faces, corner_uv)
        for name, acc in pr['attributes'].items():
            data = g.accessor(acc)
            g.set_accessor(acc, uv if name == 'TEXCOORD_0' else data[srcv])
        g.set_accessor(pr['indices'], idx.reshape(-1))
        return len(srcv)

    print('LOD0 vertices', len(p0), '->', rebuild(node['mesh'], uv0_tri))
    print('LOD0 shadow vertices ->', rebuild(shadows[0], uv0_tri))
    pr1 = doc['meshes'][lods[0]]['primitives'][0]
    p1 = g.accessor(pr1['attributes']['POSITION']).astype(np.float64)
    f1 = g.accessor(pr1['indices']).reshape(-1, 3).astype(np.int64)
    uv1, worst = lod1_uvs(p0, f0, uv0_tri, chart, p1, f1, None)
    print(f'LOD1 corner projection: worst distance {worst * 1000:.1f} mm')
    print('LOD1 vertices', len(p1), '->', rebuild(lods[0], uv1))
    print('LOD1 shadow vertices ->', rebuild(shadows[1], uv1))

    material = doc['materials'][pr0['material']]
    pbr = material['pbrMetallicRoughness']
    images = {'basecolor': pbr['baseColorTexture']['index'], 'metal_rough': pbr['metallicRoughnessTexture']['index'],
              'normal': material['normalTexture']['index'], 'region_mask': material['extras']['openyamm_region_mask']['index']}
    for kind, texture in images.items():
        path = f'{maps_prefix}_{kind}.png'
        g.set_image(doc['textures'][texture]['source'], open(path, 'rb').read(), name=Path(path).stem)
    g.save(dst)

    # far LODs: maps again from the new LOD0, on their own (unchanged) geometry and UVs
    g = Glb(dst)
    doc = g.doc
    lod0 = doc['meshes'][next(n for n in doc['nodes'] if n.get('name') == NODE and 'mesh' in n)['mesh']]
    binary = g.bin
    for level in (2, 3):
        pr = doc['meshes'][lods[level - 1]]['primitives'][0]
        corners = TT.source_faces(doc, binary, pr)
        uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
        mat = doc['materials'][pr['material']]
        kinds = TT.material_maps(mat)
        size = g.image(doc['textures'][kinds['basecolor']]['source']).size[0]
        maps, coverage = TT.transfer(doc, binary, lod0['primitives'][0], pr, corners, uv[corners], size)
        print(f'LOD{level}: {size}px, {coverage:.0%} covered')
        for kind, picture in maps.items():
            image_index = doc['textures'][kinds[kind]]['source']
            g.set_image(image_index, png(picture))
    g.save(dst)
    print('WROTE', dst)


if __name__ == '__main__':
    main()
