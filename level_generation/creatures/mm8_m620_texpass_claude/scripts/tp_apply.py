"""Puts the texture-pass layout and maps on an installed GLB (generalised from mm8_m480_texpass_claude's
apply_layout.py). Only UVs (and the vertex splits they need), texture images and the texture references of the atlas
materials change; nodes, skin, clips, materials' other fields, variants, ramps and every other attribute are carried
over from the input GLB.

1. LOD0 atlas primitives (texpass.json atlas_prims): the layout's corner UVs, vertices split at the new seams. The
   input's LOD0 must equal work/lod0_before.npz (the mesh the layout was made on).
2. LOD1 primitives of the same index: each LOD1 triangle takes the LOD0 chart (of the same primitive) under its
   centre, each corner the UV of the nearest point of that chart.
3. Shadow meshes of LOD0 and LOD1: triangles matched to the visible ones by corner positions take their new UVs.
4. New images for the main material's maps (<maps prefix>_{basecolor,metal_rough,normal,region_mask,burn_map}.png);
   every material (default and variants) of the atlas primitives at LOD0/LOD1 points at them: the main material's
   kinds all, the other primitives' materials the kinds they had (a claws set without region mask stays without).
   Textures and images nothing uses any more are dropped.
5. LOD2/LOD3 keep geometry and UVs; their own maps are transferred again from the new LOD0 per primitive with
   lod_repair_claude/scripts/transfer_textures.py at their installed sizes.

Usage: tp_apply.py <in glb> <layout npz> <maps prefix> <out glb> [--copy]
--copy: the input is a copy of the reference body with its own LOD0 (an MM7 copy of an MM8 GLB, reduced separately):
its LOD0 is projected from the reference LOD0 charts as LOD1 is; LOD1 too (texpass.json names the copy's node).
"""
import sys
import types
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

import tp_common as C
from glb import Glb, png
import texture_quality as TQ
import texlib
from scipy import ndimage

sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(C.CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

KINDS = ('basecolor', 'metal_rough', 'normal', 'region_mask', 'burn_map')
TEXTURE_KEYS = ('baseColorTexture', 'metallicRoughnessTexture', 'normalTexture', 'occlusionTexture',
                'emissiveTexture')


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


def lod1_uvs(p0, f0, uv0_tri, chart, p1, f1):
    n0f = np.cross(p0[f0[:, 1]] - p0[f0[:, 0]], p0[f0[:, 2]] - p0[f0[:, 0]])
    n0f /= np.maximum(np.linalg.norm(n0f, axis=1, keepdims=True), 1e-12)
    tree = cKDTree(p0[f0].mean(1))
    centre = p1[f1].mean(1)
    fn = np.cross(p1[f1[:, 1]] - p1[f1[:, 0]], p1[f1[:, 2]] - p1[f1[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    K = min(32, len(f0))
    _, cand = tree.query(centre, k=K)
    cand = cand.reshape(len(f1), -1)
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


def corner_keys(p, f):
    return [tuple(sorted(map(tuple, np.round(p[t], 6)))) for t in f]


def texture_refs(material):
    """(container dict, key) of every texture reference in a material."""
    refs = []
    pbr = material.get('pbrMetallicRoughness', {})
    for holder in (pbr, material):
        for key in TEXTURE_KEYS:
            if isinstance(holder.get(key), dict) and 'index' in holder[key]:
                refs.append((holder, key))
    for key, value in material.get('extras', {}).items():
        if isinstance(value, dict) and 'index' in value:
            refs.append((material['extras'], key))
    return refs


def drop_unused_textures(doc):
    used = sorted({holder[key]['index'] for m in doc['materials'] for holder, key in texture_refs(m)})
    remap = {old: new for new, old in enumerate(used)}
    doc['textures'] = [doc['textures'][i] for i in used]
    for m in doc['materials']:
        for holder, key in texture_refs(m):
            holder[key]['index'] = remap[holder[key]['index']]
    images = sorted({t['source'] for t in doc['textures']})
    iremap = {old: new for new, old in enumerate(images)}
    doc['images'] = [doc['images'][i] for i in images]
    for t in doc['textures']:
        t['source'] = iremap[t['source']]
    return len(remap), len(images)


def main():
    cfg = C.config()
    src, layout_path, maps_prefix, dst = sys.argv[1:5]
    copy_mode = '--copy' in sys.argv[5:]
    g = Glb(src)
    doc = g.doc
    mi = C.lod0_mesh_index(doc, cfg['node'])
    lod0 = doc['meshes'][mi]
    lods = lod0['extras']['openyamm_lods']
    shadows = lod0['extras'].get('openyamm_shadow_lods', [])
    before = np.load(C.lod0_path())
    layout = np.load(layout_path)
    assert (layout['tri'] == before['tri']).all()
    prims = cfg['atlas_prims']

    def prim_geometry(mesh_index, pi):
        pr = doc['meshes'][mesh_index]['primitives'][pi]
        return (g.accessor(pr['attributes']['POSITION']).astype(np.float64),
                g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64))

    def rebuild(mesh_index, pi, corner_uv):
        pr = doc['meshes'][mesh_index]['primitives'][pi]
        faces = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
        srcv, uv, idx = split_vertices(faces, corner_uv)
        for name, acc in pr['attributes'].items():
            data = g.accessor(acc)
            g.set_accessor(acc, uv if name == 'TEXCOORD_0' else data[srcv])
        g.set_accessor(pr['indices'], idx.reshape(-1))
        return len(srcv)

    new_uv = {0: {}, 1: {}}        # level -> prim -> (positions, faces, corner uvs) for the shadow match
    for k, pi in enumerate(prims):
        sel = before['prim'] == pi
        off = before['offsets'][k]
        rf = before['tri'][sel] - off
        rp = before['pos'][off:off + int(rf.max()) + 1]
        uvr = layout['uv'][sel]
        chart = TQ.islands(uvr, rp[rf])
        p0, f0 = prim_geometry(mi, pi)
        if copy_mode:
            # a copy of the reference body with its own reduction (MM7 copy of an MM8 GLB): LOD0 projected too
            uv0, worst0 = lod1_uvs(rp, rf, uvr, chart, p0, f0)
            print(f'prim {pi}: LOD0 projected from the reference, worst {worst0 * 1000:.1f} mm')
        else:
            assert (f0 == rf).all() and np.allclose(p0, rp, atol=1e-6), \
                f'LOD0 primitive {pi} differs from the mesh the layout was made on'
            uv0 = uvr
        new_uv[0][pi] = (p0, f0, uv0)
        p1, f1 = prim_geometry(lods[0], pi)
        assert doc['meshes'][lods[0]]['primitives'][pi]['material'] == lod0['primitives'][pi]['material']
        uv1, worst = lod1_uvs(rp, rf, uvr, chart, p1, f1)
        new_uv[1][pi] = (p1, f1, uv1)
        print(f'prim {pi}: LOD1 corner projection worst {worst * 1000:.1f} mm')
        print(f'prim {pi}: LOD0 vertices', len(p0), '->', rebuild(mi, pi, uv0))
        print(f'prim {pi}: LOD1 vertices', len(p1), '->', rebuild(lods[0], pi, uv1))

    for level, shadow in enumerate(shadows[:2]):
        lookup = {}
        for pi, (p, f, uv) in new_uv[level].items():
            for t, key in enumerate(corner_keys(p, f)):
                lookup[key] = (p[f[t]], uv[t])
        for spi, pr in enumerate(doc['meshes'][shadow]['primitives']):
            ps = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
            fs = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
            old = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)[fs]
            corner_uv = old.copy()
            hit = 0
            for t, key in enumerate(corner_keys(ps, fs)):
                found = lookup.get(key)
                if found is None:
                    continue
                pos, uv = found
                for c in range(3):
                    j = int(np.argmin(np.linalg.norm(pos - ps[fs[t, c]], axis=1)))
                    corner_uv[t, c] = uv[j]
                hit += 1
            if hit < len(fs) and spi in new_uv[level]:
                # a shadow copy with offset positions (MM8 Minotaur LOD1): same faces in the same order -> same UVs
                p_l, f_l, uv_l = new_uv[level][spi]
                if len(f_l) == len(fs) and len(p_l) == len(ps) and (f_l == fs).all():
                    corner_uv = uv_l.copy()
                    hit = len(fs)
                    print(f'shadow LOD{level} prim {spi}: matched by face order (positions offset)')
            print(f'shadow LOD{level} prim {spi}: {hit}/{len(fs)} triangles matched')
            rebuild(shadow, spi, corner_uv)

    # meshes outside the LOD chain that share an atlas material and read its old layout (the Gargoyle's Rubble):
    # each triangle takes the old-layout LOD0 triangle under its UV centroid and maps its corners through that
    # triangle's old -> new UV affine map, so it samples the same paint in the new atlas
    for follower in cfg.get('uv_followers', []):
        mesh_name, fpi, k_atlas = follower[:3]
        mesh_f = next(i for i, m in enumerate(doc['meshes']) if m.get('name') == mesh_name)
        pi = prims[k_atlas]
        sel = before['prim'] == pi
        if len(follower) > 3 and follower[3] == '3d':
            # a far LOD of the same body in bind space: projected per triangle from the new LOD0 charts, as LOD1
            off = before['offsets'][k_atlas]
            rf = before['tri'][sel] - off
            rp = before['pos'][off:off + int(rf.max()) + 1]
            pf, ff = prim_geometry(mesh_f, fpi)
            uvf, worst = lod1_uvs(rp, rf, layout['uv'][sel], TQ.islands(layout['uv'][sel], rp[rf]), pf, ff)
            print(f'follower {mesh_name} prim {fpi}: projected in 3D (worst {worst * 1000:.1f} mm)')
            rebuild(mesh_f, fpi, uvf)
            continue
        old = before['uv'][before['tri'][sel]]
        new = layout['uv'][sel]
        R = 2048
        tid, _ = texlib.raster(old, R)
        _, (iy, ix) = ndimage.distance_transform_edt(tid < 0, return_indices=True)
        tid = tid[iy, ix]
        prf = doc['meshes'][mesh_f]['primitives'][fpi]
        ff = g.accessor(prf['indices']).reshape(-1, 3).astype(np.int64)
        uf = g.accessor(prf['attributes']['TEXCOORD_0']).astype(np.float64)[ff]
        c = uf.mean(1)
        host = tid[np.clip((c[:, 1] * R).astype(int), 0, R - 1), np.clip((c[:, 0] * R).astype(int), 0, R - 1)]
        a, b_, c_ = old[host, 0], old[host, 1], old[host, 2]
        out = np.zeros_like(uf)
        for k in range(3):
            v0, v1, v2 = b_ - a, c_ - a, uf[:, k] - a
            d00, d01, d11 = (v0 * v0).sum(-1), (v0 * v1).sum(-1), (v1 * v1).sum(-1)
            d20, d21 = (v2 * v0).sum(-1), (v2 * v1).sum(-1)
            den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-20, 1e-20, d00 * d11 - d01 * d01)
            bv = (d11 * d20 - d01 * d21) / den
            bw = (d00 * d21 - d01 * d20) / den
            out[:, k] = new[host, 0] + bv[:, None] * (new[host, 1] - new[host, 0]) + bw[:, None] * (new[host, 2] - new[host, 0])
        print(f'follower {mesh_name} prim {fpi}: {len(ff)} triangles remapped through atlas primitive {pi}')
        rebuild(mesh_f, fpi, out)

    # new images and textures for the main material's maps
    main_mat = doc['materials'][lod0['primitives'][prims[0]]['material']]
    main_maps = C.material_maps(main_mat)
    new_tex = {}
    for kind in KINDS:
        path = Path(f'{maps_prefix}_{kind}.png')
        if kind not in main_maps and not (kind == 'burn_map' and path.exists()):
            continue
        if not path.exists():
            raise SystemExit(f'missing {path}')
        doc['images'].append({'name': f"{cfg['stem']}_tp{cfg.get('tag', '')}_{kind}"})
        g.set_image(len(doc['images']) - 1, path.read_bytes())
        old_tex = main_maps.get(kind)
        sampler = {'sampler': doc['textures'][old_tex]['sampler']} \
            if old_tex is not None and 'sampler' in doc['textures'][old_tex] else {}
        doc['textures'].append({'source': len(doc['images']) - 1, **sampler})
        new_tex[kind] = len(doc['textures']) - 1
    slots = {'basecolor': ('pbr', 'baseColorTexture'), 'metal_rough': ('pbr', 'metallicRoughnessTexture'),
             'normal': ('mat', 'normalTexture'), 'region_mask': ('extras', 'openyamm_region_mask'),
             'burn_map': ('extras', 'openyamm_burn_map')}
    atlas_mats = set()
    for mesh_index in (mi, lods[0]):
        for pi in prims:
            atlas_mats.update(C.primitive_materials(doc['meshes'][mesh_index]['primitives'][pi]))
    for m in sorted(atlas_mats):
        mat = doc['materials'][m]
        had = C.material_maps(mat)
        for kind, tex in new_tex.items():
            if kind not in had and kind not in ('basecolor', 'metal_rough', 'normal'):
                continue
            where, key = slots[kind]
            holder = mat.setdefault('pbrMetallicRoughness', {}) if where == 'pbr' else \
                mat.setdefault('extras', {}) if where == 'extras' else mat
            info = dict(holder.get(key, {}))
            info['index'] = tex
            holder[key] = info
        print('material', mat.get('name'), 'now', sorted(C.material_maps(mat)))
    print('textures, images kept:', drop_unused_textures(doc))
    g.save(dst)

    # far LODs: their own maps again from the new LOD0, per primitive, on their own geometry and UVs
    g = Glb(dst)
    doc = g.doc
    lod0 = doc['meshes'][C.lod0_mesh_index(doc, cfg['node'])]
    binary = g.bin
    for level in (2, 3):
        if len(lods) < level:
            continue
        for pi in prims:
            if pi >= len(doc['meshes'][lods[level - 1]]['primitives']):
                print(f'LOD{level}: no primitive {pi} (m620 head set: the far chain is rebuilt by lod_repair_claude)')
                continue
            pr = doc['meshes'][lods[level - 1]]['primitives'][pi]
            if pr['material'] in atlas_mats:
                print(f'LOD{level} prim {pi}: shares the atlas material; its UVs follow (uv_followers), no refill')
                continue
            corners = TT.source_faces(doc, binary, pr)
            uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
            kinds = TT.material_maps(doc['materials'][pr['material']])
            size = g.image(doc['textures'][kinds['basecolor']]['source']).size[0]
            maps, coverage = TT.transfer(doc, binary, lod0['primitives'][pi], pr, corners, uv[corners], size)
            print(f'LOD{level} prim {pi}: {size}px, {coverage:.0%} covered, maps {sorted(maps)}')
            for kind, picture in maps.items():
                if kind in kinds:
                    g.set_image(doc['textures'][kinds[kind]]['source'], png(picture))
    g.save(dst)
    print('WROTE', dst)


if __name__ == '__main__':
    main()
