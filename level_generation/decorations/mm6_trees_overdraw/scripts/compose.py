#!/usr/bin/env python3
"""Step 3: write work/<id>/mm6_deco_<id>.glb from work/<id>/installed.glb and work/<id>/shell.npz (system Python).

Per LOD 0..2 the leaf primitive (Leaves; LOD2 LeavesFar) keeps only the selected cards (their vertices copied as
they are; `cards.grow[lod]` scales each kept card about its centre) and gains a Shell primitive. Bark, fruit, moss,
the impostor, all other materials and images stay byte-identical. Material Shell: opaque, single-sided,
roughness 0.95, metallic 0, openyamm_wind = the leaves' value, openyamm_specular 0.05; base colour = the model's own
impostor texture (shell.texture 'impostor', default; 'white' = the MM8 shells' white 8x8) and the flat normal map of
the MM8 shells (`mm8_deco_tree14.glb`, same bytes, so the cook stores it once).
Usage: compose.py <id>"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb, common

tid = sys.argv[1]
spec = common.load(tid); W = spec['work']; C = spec['cards']
m = glb.read(os.path.join(W, 'installed.glb'))
sh = np.load(os.path.join(W, 'shell.npz'))
ref = glb.read(os.path.join(common.REPO, 'assets_source', 'engine', 'models', 'mm8_deco_tree14.glb'))
rmat = ref.doc['materials'][ref.material_index('Shell')]


def ref_image(tex_index):
    return ref.images[ref.doc['textures'][tex_index]['source']]


assert 'Shell' not in [x['name'] for x in m.doc['materials']], 'installed model already has a shell'
leaf_mat = m.doc['materials'][m.material_index('Leaves')]
normal_tex = m.add_texture(m.add_image('shell_normal', ref_image(rmat['normalTexture']['index'])))
TEXTURE = spec['shell'].get('texture', 'impostor')
imp_mesh = m.mesh_chain()[-1]
imp_prim = m.doc['meshes'][imp_mesh]['primitives'][0]
assert m.doc['materials'][imp_prim['material']]['name'] == 'Impostor'
if TEXTURE == 'impostor':
    # the shell shows the tree's own impostor texture (leafy, already in the GLB: no new image): seen through a gap
    # it reads as foliage deeper in the crown, not as a smooth wash. UV: the impostor quad's affine (x, y) -> uv map,
    # with x replaced by the arc around the crown folded every quarter turn (s = rho * tri(theta)), so the sides and
    # the back keep the leaf scale of the front.
    base_tex = m.doc['materials'][imp_prim['material']]['pbrMetallicRoughness']['baseColorTexture']['index']
    qp = m.get(imp_prim['attributes']['POSITION']); quv = m.get(imp_prim['attributes']['TEXCOORD_0'])
    A = np.c_[qp[:, 0], qp[:, 1], np.ones(len(qp))]
    affine, *_ = np.linalg.lstsq(A, quv, rcond=None)
    from PIL import Image
    import io
    im = np.asarray(Image.open(io.BytesIO(m.images[m.doc['textures'][base_tex]['source']])).convert('RGBA')) / 255.0
    ok = im[..., 3] > 0.5
    lin = np.where(im[..., :3] <= 0.04045, im[..., :3] / 12.92, ((im[..., :3] + 0.055) / 1.055) ** 2.4)
    tex_mean = lin[ok].mean(0)          # the shell colour is divided by it: texture x COLOR_0 ~ the replaced cards
    # texels under the alpha cutoff are near black (sky gaps of the impostor, around the trunk): a vertex landing
    # there moves to the nearest opaque texel of the crown
    from scipy import ndimage
    _, (near_y, near_x) = ndimage.distance_transform_edt(~ok, return_indices=True)
    tex_h, tex_w = ok.shape
else:
    base_tex = m.add_texture(m.add_image('shell_basecolor', ref_image(rmat['pbrMetallicRoughness']['baseColorTexture']['index'])))
    tex_mean = np.ones(3)


def shell_uv(v):
    if TEXTURE != 'impostor':
        return np.stack([v[:, 0] + v[:, 2] * 0.5, v[:, 1]], 1) / 2.0     # white base colour, flat normal map
    rho = np.hypot(v[:, 0], v[:, 2]); th = np.arctan2(v[:, 0], v[:, 2])
    tri = np.arcsin(np.sin(th)) / (np.pi / 2)        # -1..1, folded every quarter turn
    s = rho * tri
    shrink = spec['shell'].get('uv_shrink', 0.85)    # toward the crown centre: the impostor's denser inner foliage
    cy = float(np.mean(v[:, 1]))
    dy = v[:, 1] - cy
    if spec['shell'].get('uv_fold', True):     # the underside shows the impostor's lit upper crown (seen from
        dy = np.abs(dy)                        # under the tree the leaves are lit, the impostor's lower rim is not)
    uv = np.c_[s * shrink, cy + dy * shrink, np.ones(len(v))] @ affine
    px = np.clip((uv[:, 0] * tex_w).astype(int), 0, tex_w - 1); py = np.clip((uv[:, 1] * tex_h).astype(int), 0, tex_h - 1)
    bad = ~ok[py, px]
    uv[bad, 0] = (near_x[py[bad], px[bad]] + 0.5) / tex_w; uv[bad, 1] = (near_y[py[bad], px[bad]] + 0.5) / tex_h
    return uv
m.doc['materials'].append({'name': 'Shell', 'doubleSided': False,
                           'extras': {'openyamm_wind': leaf_mat['extras']['openyamm_wind'], 'openyamm_specular': 0.05},
                           'normalTexture': {'index': normal_tex},
                           'pbrMetallicRoughness': {'baseColorTexture': {'index': base_tex}, 'metallicFactor': 0,
                                                    'roughnessFactor': 0.95}})
shell_mat = len(m.doc['materials']) - 1
chain = m.mesh_chain()
for lod in (0, 1, 2):
    mesh = chain[lod]
    prim = m.primitive(mesh, 'LeavesFar') if lod == 2 else None
    prim = prim or m.primitive(mesh, 'Leaves')
    keep = sh[f'l{lod}_keep'].copy()
    grow = C['grow'][lod] if isinstance(C['grow'], list) else C['grow']
    a = prim['attributes']
    nv = len(m.arrays[a['POSITION']]); assert nv == 4 * len(keep)
    pin = np.zeros(len(keep), bool)
    if lod == 0:          # cards on the LOD0 bounds stay as they are (the engine scales the model by these bounds)
        allp = np.concatenate([m.get(p['attributes']['POSITION']) for p in m.doc['meshes'][mesh]['primitives']])
        lo, hi = allp.min(0), allp.max(0)
        q = m.get(a['POSITION']).reshape(-1, 4, 3)
        pin = (np.isclose(q, lo, atol=1e-6) | np.isclose(q, hi, atol=1e-6)).any((1, 2))
        print(f'COMPOSE LOD0 bound cards {int(pin.sum())} (re-kept {int((pin & ~keep).sum())})')
        keep |= pin
    vsel = np.repeat(keep, 4)
    old_idx = m.arrays[prim['indices']].reshape(-1, 3)
    # cards are 4 consecutive vertices and 2 triangles; keep each kept card's own triangles
    tri_card = old_idx[:, 0] // 4
    assert np.all(old_idx // 4 == tri_card[:, None])
    new_of_card = np.cumsum(keep) - 1
    tri_keep = keep[tri_card]
    idx = old_idx[tri_keep] - 4 * tri_card[tri_keep, None] + 4 * new_of_card[tri_card[tri_keep], None]
    new_attrs = {}
    for key, acc in a.items():
        arr = m.arrays[acc][vsel]
        if key == 'POSITION' and grow != 1.0:
            q = arr.reshape(-1, 4, 3).astype(np.float64); c = q.mean(1, keepdims=True)
            g = np.where(pin[keep], 1.0, grow)[:, None, None]
            arr = (c + (q - c) * g).reshape(-1, 3).astype(np.float32)
        if key == 'COLOR_0' and C.get('vc_floor'):
            # leaf vertex colours floored (max channel, hue kept): the engine's leaf shader adds no sky reflection
            # on alpha-tested leaves, so deep cards left in view would read as black
            f = np.iinfo(arr.dtype).max if arr.dtype != np.float32 else 1.0
            rgb = arr[:, :3].astype(np.float64) / f; mx = rgb.max(1, keepdims=True)
            rgb = np.where(mx < C['vc_floor'], rgb * (C['vc_floor'] / np.maximum(mx, 1e-6)), rgb)
            arr = arr.copy(); arr[:, :3] = np.round(rgb * f).astype(arr.dtype) if f != 1.0 else rgb
        src = m.doc['accessors'][acc]
        new_attrs[key] = m.add_accessor(arr, normalized=bool(src.get('normalized')), minmax=key == 'POSITION')
    prim['attributes'] = new_attrs
    prim['indices'] = m.add_accessor(idx.reshape(-1).astype(m.arrays[prim['indices']].dtype))
    verts = sh[f'l{lod}_verts']; faces = sh[f'l{lod}_faces']; normals = sh[f'l{lod}_normals']
    value = spec['shell']['value']
    value = value[lod] if isinstance(value, list) and len(value) == 3 and isinstance(value[0], list) else value
    base_col = sh[f'l{lod}_colours']
    # floor at `shell.floor` x the median: a deep pit of the shell (an open crown underside) reads as dark foliage,
    # not as a black hole
    base_col = np.maximum(base_col, spec['shell'].get('floor', 0.8) * np.median(base_col, axis=0))
    col = np.concatenate([np.clip(base_col / tex_mean * np.asarray(value, float), 0, 1),
                          np.ones((len(verts), 1))], 1)
    uv = shell_uv(verts)
    m.add_primitive(mesh, shell_mat, verts, normals, uv, col, faces)
    print(f'COMPOSE LOD{lod} cards {len(keep)} -> {int(keep.sum())}, shell tris {len(faces)}')
# the LOD0 bounds must not change (the engine scales by them; the food-tree pair must stay identical)
out = os.path.join(W, spec['glb'])
m.write(out)
new = glb.read(out); old = glb.read(os.path.join(W, 'installed.glb'))


def bounds(model):
    ps = [model.get(p['attributes']['POSITION']) for p in model.doc['meshes'][model.mesh_chain()[0]]['primitives']]
    ps = np.concatenate(ps); return ps.min(0), ps.max(0)


b0, b1 = bounds(old), bounds(new)
print('BOUNDS LOD0 installed', np.round(b0[0], 4).tolist(), np.round(b0[1], 4).tolist(), ' new',
      np.round(b1[0], 4).tolist(), np.round(b1[1], 4).tolist())
for lod, mi in enumerate(new.mesh_chain()):
    print(f'TRIS LOD{lod}', {new.doc['materials'][p['material']]['name']: int(new.doc['accessors'][p['indices']]['count'] // 3)
                            for p in new.doc['meshes'][mi]['primitives']},
          'total', sum(new.doc['accessors'][p['indices']]['count'] // 3 for p in new.doc['meshes'][mi]['primitives']),
          'before', sum(old.doc['accessors'][p['indices']]['count'] // 3 for p in old.doc['meshes'][old.mesh_chain()[lod]]['primitives']))
print('WROTE', out, os.path.getsize(out))
