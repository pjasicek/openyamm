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
    sets = tp.part_images(doc)
    body_set = sets[0]

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

    def corners_of(mesh_index, prim=0):
        pr = doc['meshes'][mesh_index]['primitives'][prim]
        return g.accessor(pr['attributes']['POSITION']).astype(np.float64)[g.accessor(pr['indices']).reshape(-1, 3)]

    def old_uv(mesh_index, prim=0):
        pr = doc['meshes'][mesh_index]['primitives'][prim]
        return g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)[g.accessor(pr['indices']).reshape(-1, 3)]

    def rebuild(mesh_index, corner_uv, prim=0, like=None):
        pr = doc['meshes'][mesh_index]['primitives'][prim]
        faces = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
        assert len(faces) == len(corner_uv)
        if like is not None:   # a shadow copy: same triangles as its colour mesh (shadow LODs are shrunk a few mm)
            ext = float(np.ptp(like.reshape(-1, 3), 0).max())
            # shadow insets up to 30 mm (Ogre Warrior m440's finish_runtime.py cap)
            assert np.abs(g.accessor(pr['attributes']['POSITION'])[faces] - like).max() < max(0.015 * ext, 0.031), \
                'shadow differs'
        srcv, uv, idx = split_vertices(faces, corner_uv)
        for name, acc in pr['attributes'].items():
            data = g.accessor(acc)
            g.set_accessor(acc, uv if name == 'TEXCOORD_0' else data[srcv])
        g.set_accessor(pr['indices'], idx.reshape(-1))
        return len(srcv)

    def rebuild_shadow(mesh_index, uvs, likes):
        """A shadow mesh: one primitive per colour primitive, or one primitive holding them all in order."""
        n = len(doc['meshes'][mesh_index]['primitives'])
        if n == len(uvs):
            return [rebuild(mesh_index, u, j, c) for j, (u, c) in enumerate(zip(uvs, likes))]
        assert n == 1, 'shadow primitives do not match the colour primitives'
        return rebuild(mesh_index, np.concatenate(uvs), 0, np.concatenate(likes))

    part_uv, start = [], 0
    for k in range(len(prims)):
        n = int((layout['part'] == k).sum())
        part_uv.append(layout['uv'][start:start + n])
        start += n
    by_mesh = {}
    for k, (mi, pi) in enumerate(prims):
        by_mesh.setdefault(mi, []).append(k)
    transfer = []
    for mi, ks in by_mesh.items():
        nprim = len(doc['meshes'][mi]['primitives'])
        kprim = {prims[k][1]: k for k in ks}          # primitive index -> layout part (others keep their UVs)
        extras = doc['meshes'][mi].get('extras', {})
        lods, shadows = extras.get('openyamm_lods', []), extras.get('openyamm_shadow_lods', [])
        likes = [corners_of(mi, j) for j in range(nprim)]
        uvs0 = [part_uv[kprim[j]] if j in kprim else old_uv(mi, j) for j in range(nprim)]
        for j, k in kprim.items():
            print(doc['meshes'][mi]['name'], j, 'vertices ->', rebuild(mi, part_uv[k], j))
        if shadows:
            print(' shadow', doc['meshes'][shadows[0]]['name'], '->', rebuild_shadow(shadows[0], uvs0, likes))
        for level, lm in enumerate(lods, start=1):
            assert len(doc['meshes'][lm]['primitives']) == nprim, 'LOD primitives do not match LOD0'
            uvs, lod_likes, projected = [], [], 0
            for j in range(nprim):
                pr = doc['meshes'][lm]['primitives'][j]
                lod_likes.append(corners_of(lm, j))
                k = kprim.get(j)
                if k is None:
                    uvs.append(old_uv(lm, j))                                  # not laid out: untouched
                    continue
                if tp.material_images(doc, pr['material']).get('basecolor') != sets[k]['basecolor']:
                    transfer.append((level, lm, j, mi, j))                     # own far-LOD maps
                    uvs.append(old_uv(lm, j))
                    continue
                f0 = before['tri'][layout['part'] == k]
                p1 = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
                f1 = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
                chart = TQ.islands(part_uv[k], before['pos'][f0])
                uv1, worst = project_uvs(before['pos'], f0, part_uv[k], chart, p1, f1)
                print(f'LOD{level} prim {j} projected: worst distance {worst * 1000:.1f} mm, vertices', len(p1), '->',
                      rebuild(lm, uv1, j))
                uvs.append(uv1)
                projected += 1
            if level < len(shadows) and projected:      # untouched when every primitive kept its UVs
                print(f' LOD{level} shadow ->', rebuild_shadow(shadows[level], uvs, lod_likes))

    for kind, image in body_set.items():
        g.set_image(image, open(f'{maps_prefix}_{kind}.png', 'rb').read(), name=doc['images'][image].get('name'))
    if tp.CFG.get('merge_sets'):
        # the other layout primitives' materials (every variant) sample the merged atlas: their textures take the body
        # set's images; images nothing references any more are dropped
        remap = {}
        for other in sets[1:]:
            for kind, image in other.items():
                if image != body_set.get(kind):
                    assert kind in body_set, f'merged set lacks {kind}'
                    remap[image] = body_set[kind]
        for tex in doc['textures']:
            tex['source'] = remap.get(tex['source'], tex['source'])
        used = sorted({t['source'] for t in doc['textures']})
        index = {old: new for new, old in enumerate(used)}
        print('merged sets: images', len(doc['images']), '->', len(used), 'dropped', [doc['images'][i].get('name') for i in
                                                                                  range(len(doc['images'])) if i not in index])
        doc['images'] = [doc['images'][i] for i in used]
        for tex in doc['textures']:
            tex['source'] = index[tex['source']]
    g.save(dst)

    if transfer:
        g = Glb(dst)
        doc = g.doc
        for level, lm, j, mi, pi in transfer:
            pr = doc['meshes'][lm]['primitives'][j]
            corners = TT.source_faces(doc, g.bin, pr)
            uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
            kinds = TT.material_maps(doc['materials'][pr['material']])
            size = g.image(doc['textures'][kinds['basecolor']]['source']).size[0]
            maps, coverage = TT.transfer(doc, g.bin, doc['meshes'][mi]['primitives'][pi], pr, corners, uv[corners], size)
            print(f'LOD{level} prim {j}: maps transferred at {size}px, {coverage:.0%} covered')
            for kind, picture in maps.items():
                g.set_image(doc['textures'][kinds[kind]]['source'], png(picture))
        g.save(dst)
    print('WROTE', dst)


if __name__ == '__main__':
    main()
