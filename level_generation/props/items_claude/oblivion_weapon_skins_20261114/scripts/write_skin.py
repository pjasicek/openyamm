#!/usr/bin/env python3
"""The skin GLB from the template (README.md): the template's JSON kept whole (nodes, their names and transforms, the
bow's animations, morph and arrow, the arrow's material) with the weapon primitive's vertex data rebuilt on the new UVs
and its material's three images replaced.

Each new vertex is a template vertex with a new UV (a vertex on a new seam is split): positions, normals and morph
deltas are the template's, the triangles are the template's in its order, wound with their normals (see below).
Checked: the same triangles by position.

Usage: python3 write_skin.py <template> <tier> <maps dir with basecolor.png, normal.png, mr.png> <out.glb>
"""
import copy
import io
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
import glb_io

name, tier, maps, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
doc, binary = glb_io.read(os.path.join(REPO, 'assets_source', 'engine', 'view_model', f'{name}.glb'))
views = [glb_io.view_bytes(doc, binary, i) for i in range(len(doc['bufferViews']))]
new = copy.deepcopy(doc)
mesh_index, prim = glb_io.mesh_primitive(doc, 'Bow' if name == 'w_bow' else None)
nprim = new['meshes'][mesh_index]['primitives'][0]
# w_staff_grip is w_staff's mesh under a node moved up the shaft (same triangles and vertices): it takes the staff's
# layout and paint.
UV_FROM = {'w_staff_grip': 'w_staff'}
uv = np.load(os.path.join(PROJECT, 'work', UV_FROM.get(name, name), 'uv_template.npy'))
tri = glb_io.accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)

# New vertices: (template vertex, new uv) pairs.
keys = np.concatenate([tri.reshape(-1, 1).astype(np.float64), np.round(uv.reshape(-1, 2), 6)], 1)
unique, first, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
inverse = inverse.ravel()
source = unique[:, 0].astype(np.int64)
new_uv = uv.reshape(-1, 2)[first].astype(np.float32)
# The skins wind with their normals (the engine culls by winding). The templates as exported wound against them (the
# guard and pommel drawn from behind, near black; measured 2026-11-14) until fix_winding.py turned them; a template
# still wound the old way is turned here.
order = [0, 1, 2] if glb_io.share_wound_with_normals(doc, binary, prim) >= 0.5 else [0, 2, 1]
indices = inverse.reshape(-1, 3)[:, order].astype(np.uint32)

used = {}


def replace(accessor_index, array, component=5126):
    a = new['accessors'][accessor_index]
    view = a['bufferView']
    users = [i for i, other in enumerate(doc['accessors']) if other.get('bufferView') == view]
    assert users == [accessor_index] and 'byteStride' not in doc['bufferViews'][view], 'shared or strided view'
    a['count'] = int(len(array))
    a['componentType'] = component
    a.pop('byteOffset', None)
    if a['type'] in ('VEC3',) and component == 5126:
        a['min'] = array.min(0).astype(float).tolist()
        a['max'] = array.max(0).astype(float).tolist()
    else:
        a.pop('min', None)
        a.pop('max', None)
    views[view] = np.ascontiguousarray(array).tobytes()
    used[view] = True


for attribute, accessor in prim['attributes'].items():
    data = glb_io.accessor(doc, binary, accessor)
    replace(accessor, new_uv if attribute == 'TEXCOORD_0' else np.asarray(data)[source].astype(data.dtype))
for target in prim.get('targets', []):
    for attribute, accessor in target.items():
        data = glb_io.accessor(doc, binary, accessor)
        replace(accessor, np.asarray(data)[source].astype(data.dtype))
replace(prim['indices'], indices.ravel(), 5125)

# The bow's arrow keeps its texture but is wound with its normals too.
for other_index, mesh in enumerate(doc['meshes']):
    if other_index == mesh_index:
        continue
    other = mesh['primitives'][0]
    if glb_io.share_wound_with_normals(doc, binary, other) >= 0.5:
        continue
    flipped = np.array(glb_io.accessor(doc, binary, other['indices'])).reshape(-1, 3)[:, [0, 2, 1]]
    replace(other['indices'], np.ascontiguousarray(flipped.ravel()), new['accessors'][other['indices']]['componentType'])

# Check: the same triangles (sorted corner positions) as the template.
pos = glb_io.accessor(doc, binary, prim['attributes']['POSITION'])
old_set = sorted(tuple(sorted(map(tuple, np.round(pos[t], 4)))) for t in tri)
new_pos = pos[source]
new_set = sorted(tuple(sorted(map(tuple, np.round(new_pos[t], 4)))) for t in indices.astype(np.int64))
assert old_set == new_set, 'triangles changed'

# Images and the material.
material = new['materials'][prim['material']]
pbr = material['pbrMetallicRoughness']
for texture, file in ((pbr['baseColorTexture']['index'], 'basecolor.png'), (material['normalTexture']['index'],
                      'normal.png'), (pbr['metallicRoughnessTexture']['index'], 'mr.png')):
    image = new['images'][new['textures'][texture]['source']]
    users = [i for i, t in enumerate(new['textures']) if t['source'] == new['textures'][texture]['source']]
    assert users == [texture], 'shared image'
    buffer = io.BytesIO()
    Image.open(os.path.join(maps, file)).convert('RGB').save(buffer, 'PNG', optimize=True)
    views[image['bufferView']] = buffer.getvalue()
    image['name'] = f'{name}_t{tier}_{os.path.splitext(file)[0]}'
    image['mimeType'] = 'image/png'
# Legendary rune inlays (post.py RUNES): emissive.png as the emissive texture, factor 1 (the glow is in the image).
emissive = os.path.join(maps, 'emissive.png')
if os.path.exists(emissive):
    buffer = io.BytesIO()
    Image.open(emissive).convert('RGB').save(buffer, 'PNG', optimize=True)
    views.append(buffer.getvalue())
    new['bufferViews'].append({'buffer': 0, 'byteOffset': 0, 'byteLength': 0})
    new['images'].append({'name': f'{name}_t{tier}_emissive', 'mimeType': 'image/png',
                          'bufferView': len(new['bufferViews']) - 1})
    sampler = new['textures'][pbr['baseColorTexture']['index']].get('sampler')
    texture = {'source': len(new['images']) - 1}
    if sampler is not None:
        texture['sampler'] = sampler
    new['textures'].append(texture)
    material['emissiveTexture'] = {'index': len(new['textures']) - 1}
    material['emissiveFactor'] = [1.0, 1.0, 1.0]
    # post.py EMISSIVE_STRENGTH (the legendary bow): brighter than factor 1 allows, through
    # KHR_materials_emissive_strength (the engine accepts 0..16).
    strength_path = os.path.join(maps, 'emissive.json')
    if os.path.exists(strength_path):
        import json
        strength = float(json.load(open(strength_path))['strength'])
        material.setdefault('extensions', {})['KHR_materials_emissive_strength'] = {'emissiveStrength': strength}
        used_ext = new.setdefault('extensionsUsed', [])
        if 'KHR_materials_emissive_strength' not in used_ext:
            used_ext.append('KHR_materials_emissive_strength')
material['name'] = f'{name}_t{tier}'
pbr['metallicFactor'] = 1.0
pbr['roughnessFactor'] = 1.0
extras = material.setdefault('extras', {})
extras.pop('openyamm_specular_mask', None)
# The MR map's red channel is the baked ambient occlusion: specular fades in the fuller, at the guard and in recesses.
extras['openyamm_specular_occlusion'] = 'orm'
glb_io.write(out, new, views)
print('WRITE_SKIN', out, 'vertices', len(source), 'triangles', len(indices), 'MB %.1f' % (os.path.getsize(out) / 1e6))
