"""Puts the texture-pass layout and maps on an installed GLB (the Troll's apply_layout.py made generic through
texpass.json). Changes only UVs (and the vertex splits they need) and images; nodes, skin, clips, materials, variants,
ramps and every other attribute are carried over from the input GLB.
1. Layout meshes (LOD0 body and LOD-less extras such as wings) and their shadow copies: the layout's corner UVs,
   vertices split where the new layout has a seam. The input's triangles and positions must equal work/lod0_before.npz.
2. Lower LODs of the body (mesh extras openyamm_lods) and their shadow copies:
   - sharing the LOD0 base-colour image: each triangle takes the LOD0 chart under its centre (nearest LOD0 triangle on
     the same side), each corner the UV of the nearest point of that chart, so no triangle spans a seam;
   - with their own maps (lod_repair far LODs): geometry and UVs kept, maps transferred again from the new LOD0
     (lod_repair_claude/scripts/transfer_textures.py) at the installed sizes.
3. Images of the LOD0 material from <maps prefix>_{basecolor,metal_rough,normal,region_mask}.png.
Usage: apply.py <in glb> <maps prefix> <out glb> [layout npz (texpass.json layout)]"""
import sys
import types

import numpy as np
from scipy.spatial import cKDTree

import tp
from glb import Glb, png
import texture_quality as TQ

sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(tp.CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402


def split_vertices(corner_vid, corner_uv):
    key = np.concatenate([corner_vid.reshape(-1, 1).astype(np.float64), np.round(corner_uv.reshape(-1, 2), 7)], 1)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inverse = inverse.ravel()
    order = np.argsort(first)
    rank = np.empty_like(order)
    rank[order] = np.arange(len(order))
    src = corner_vid.reshape(-1)[first[order]]
    uv = corner_uv.reshape(-1, 2)[first[order]]
    return src, uv, rank[inverse].reshape(-1, 3)


def project_uvs(p0, f0, uv0_tri, chart, p1, f1):
    n0f = np.cross(p0[f0[:, 1]] - p0[f0[:, 0]], p0[f0[:, 2]] - p0[f0[:, 0]])
    n0f /= np.maximum(np.linalg.norm(n0f, axis=1, keepdims=True), 1e-12)
    tree = cKDTree(p0[f0].mean(1))
    centre = p1[f1].mean(1)
    fn = np.cross(p1[f1[:, 1]] - p1[f1[:, 0]], p1[f1[:, 2]] - p1[f1[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    K = min(32, len(f0))
    _, cand = tree.query(centre, k=K)
    dist, _ = TT.closest_on_triangles(centre, p0[f0[cand, 0]], p0[f0[cand, 1]], p0[f0[cand, 2]])
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
        cand_f = faces[local]
        d, w = TT.closest_on_triangles(p1[f1[t]], p0[f0[cand_f, 0]], p0[f0[cand_f, 1]], p0[f0[cand_f, 2]])
        best = np.argmin(d, 1)
        worst = max(worst, float(d[np.arange(3), best].max()))
        out[t] = (w[np.arange(3), best][:, :, None] * uv0_tri[cand_f[np.arange(3), best]]).sum(1)
    return out, worst


def main():
    src, maps_prefix, dst = sys.argv[1:4]
    layout = np.load(sys.argv[4] if len(sys.argv) > 4 else tp.HERE / tp.CFG['layout'])
    before = np.load(tp.HERE / 'work' / 'lod0_before.npz')
    g = Glb(src)
    doc = g.doc
    prims = tp.layout_prims(doc)
    body_mesh = prims[0][0]
    body_image = tp.body_images(doc)['basecolor']
    lod0 = doc['meshes'][body_mesh]
    lods = lod0.get('extras', {}).get('openyamm_lods', [])
    shadows = lod0.get('extras', {}).get('openyamm_shadow_lods', [])

    # concatenated layout surface must equal the dump
    allp, allf, off = [], [], 0
    for mi, pi in prims:
        pr = doc['meshes'][mi]['primitives'][pi]
        p = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
        allf.append(g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64) + off)
        allp.append(p)
        off += len(p)
    P, F = np.concatenate(allp), np.concatenate(allf)
    assert (F == before['tri']).all() and np.allclose(P, before['pos'], atol=1e-6), \
        'layout meshes differ from the mesh the layout was made on'
    assert (layout['tri'] == F).all()
    uv_all = layout['uv']

    def rebuild(mesh_index, corner_uv, prim=0, like=None):
        pr = doc['meshes'][mesh_index]['primitives'][prim]
        faces = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
        assert len(faces) == len(corner_uv)
        if like is not None:   # a shadow copy: same triangles as its colour mesh (shadow LODs are shrunk a few mm)
            ext = float(np.ptp(like.reshape(-1, 3), 0).max())
            assert np.abs(g.accessor(pr['attributes']['POSITION'])[faces] - like).max() < 0.015 * ext, 'shadow differs'
        srcv, uv, idx = split_vertices(faces, corner_uv)
        for name, acc in pr['attributes'].items():
            data = g.accessor(acc)
            g.set_accessor(acc, uv if name == 'TEXCOORD_0' else data[srcv])
        g.set_accessor(pr['indices'], idx.reshape(-1))
        return len(srcv)

    start = 0
    part_uv = []
    for k, (mi, pi) in enumerate(prims):
        n = (layout['part'] == k).sum()
        part_uv.append(uv_all[start:start + n])
        start += n
    for k, (mi, pi) in enumerate(prims):
        name = doc['meshes'][mi]['name']
        pr = doc['meshes'][mi]['primitives'][pi]
        corners = g.accessor(pr['attributes']['POSITION'])[g.accessor(pr['indices']).reshape(-1, 3)]
        print(name, pi, 'vertices ->', rebuild(mi, part_uv[k], pi))
        sh = doc['meshes'][mi].get('extras', {}).get('openyamm_shadow_lods', [])
        if sh:
            print(' shadow', doc['meshes'][sh[0]]['name'], '->', rebuild(sh[0], part_uv[k], pi, corners))

    # lower LODs of the body
    p0 = before['pos']
    f0 = before['tri'][layout['part'] == 0]
    uv0 = part_uv[0]
    chart = TQ.islands(uv0, p0[f0])
    transfer = []
    for level, mi in enumerate(lods, start=1):
        pr = doc['meshes'][mi]['primitives'][0]
        img = tp.material_images(doc, pr['material']).get('basecolor')
        if img != body_image:
            transfer.append((level, mi))
            continue
        p1 = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
        f1 = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
        uv1, worst = project_uvs(p0, f0, uv0, chart, p1, f1)
        print(f'LOD{level} projected: worst distance {worst * 1000:.1f} mm, vertices', len(p1), '->', rebuild(mi, uv1))
        if level < len(shadows):
            print(f' LOD{level} shadow ->', rebuild(shadows[level], uv1, 0, p1[f1]))

    material = doc['materials'][doc['meshes'][body_mesh]['primitives'][0]['material']]
    images = tp.material_images(doc, doc['meshes'][body_mesh]['primitives'][0]['material'])
    for kind, image in images.items():
        path = f'{maps_prefix}_{kind}.png'
        g.set_image(image, open(path, 'rb').read(), name=doc['images'][image].get('name'))
    g.save(dst)

    if transfer:
        g = Glb(dst)
        doc = g.doc
        lod0 = doc['meshes'][body_mesh]
        for level, mi in transfer:
            pr = doc['meshes'][mi]['primitives'][0]
            corners = TT.source_faces(doc, g.bin, pr)
            uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
            kinds = TT.material_maps(doc['materials'][pr['material']])
            size = g.image(doc['textures'][kinds['basecolor']]['source']).size[0]
            maps, coverage = TT.transfer(doc, g.bin, lod0['primitives'][0], pr, corners, uv[corners], size)
            print(f'LOD{level}: maps transferred at {size}px, {coverage:.0%} covered')
            for kind, picture in maps.items():
                g.set_image(doc['textures'][kinds[kind]]['source'], png(picture))
        g.save(dst)
    print('WROTE', dst)


if __name__ == '__main__':
    main()
