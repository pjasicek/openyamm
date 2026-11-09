"""Link authored crystal LODs using the Reactor export pattern and shared GLB helpers."""
import copy
import json
import os
import struct
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
import build_actor_lods as B  # noqa: E402

source = HERE / 'export' / 'mm8_m596_runtime_lod0.glb'
destination = HERE / 'export' / 'mm8_m596.glb'
temporary = HERE / 'export' / 'mm8_m596_lods.geometry.glb'
NODE = 'CrystalWalker'

bpy.ops.wm.open_mainfile(filepath=str(HERE / 'work' / 'crystal_walker.blend'))
rig = bpy.data.objects['CrystalRig']
for o in bpy.data.objects:
    o.hide_set(False)
    o.hide_render = False
    o.select_set(o.name.startswith('CrystalWalker_LOD') or o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(temporary), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_materials='EXPORT',
                          export_image_format='NONE')

before, original = B.read_glb(source)
node = next(n for n in before['nodes'] if n.get('name') == NODE)
mesh_index = node['mesh']
joint_names = [before['nodes'][i]['name'] for i in before['skins'][node['skin']]['joints']]
bind = list(struct.iter_unpack('<16f', B.accessor_bytes(before, original,
                                                         before['skins'][node['skin']]['inverseBindMatrices'])))
exported, payload = B.read_glb(temporary)
document = copy.deepcopy(before); binary = bytearray(original)
material_indices = {m['name']: i for i, m in enumerate(document['materials'])}
lod_indices = []
for level in (1, 2):
    name = f'{NODE}_LOD{level}'
    lower = next(n for n in exported['nodes'] if n.get('name') == name and 'mesh' in n)
    skin = exported['skins'][lower['skin']]
    remap = [joint_names.index(exported['nodes'][i]['name']) for i in skin['joints']]
    matrices = list(struct.iter_unpack('<16f', B.accessor_bytes(exported, payload, skin['inverseBindMatrices'])))
    if any(abs(a - b) > 1e-4 for index, matrix in zip(remap, matrices) for a, b in zip(bind[index], matrix)):
        raise SystemExit('LOD bind space differs from the runtime export')
    mesh = {'name': name, 'primitives': []}
    for primitive in exported['meshes'][lower['mesh']]['primitives']:
        attributes = {}
        for semantic, index in primitive['attributes'].items():
            accessor = exported['accessors'][index]
            packed = B.accessor_bytes(exported, payload, index)
            if semantic.startswith('JOINTS_'):
                code = {5121: 'B', 5123: 'H'}[accessor['componentType']]
                values = [remap[v[0]] for v in struct.iter_unpack('<' + code, packed)]
                packed = struct.pack('<' + code * len(values), *values)
            attributes[semantic] = B.append_accessor(document, binary, accessor, packed)
        mesh['primitives'].append({'attributes': attributes,
            'indices': B.append_accessor(document, binary, exported['accessors'][primitive['indices']],
                                         B.accessor_bytes(exported, payload, primitive['indices'])),
            'material': material_indices[exported['materials'][primitive['material']]['name']]})
    lod_indices.append(len(document['meshes'])); document['meshes'].append(mesh)
shadows = []
for index in [mesh_index] + lod_indices:
    shadow = B.merge_shadow(document, binary, document['meshes'][index])
    shadows.append(len(document['meshes'])); document['meshes'].append(shadow)
document['meshes'][mesh_index].setdefault('extras', {}).update(openyamm_lods=lod_indices, openyamm_shadow_lods=shadows)
counts = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
          for i in [mesh_index] + lod_indices]
if not all(a > b for a, b in zip(counts, counts[1:])):
    raise SystemExit(f'LOD triangle counts must decrease: {counts}')
B.write_glb(destination, document, binary)
temporary.unlink()
(HERE / 'export' / 'lods.json').write_text(json.dumps({'triangles': counts, 'authored': True}, indent=2) + '\n')
print('LOD triangles:', counts)
