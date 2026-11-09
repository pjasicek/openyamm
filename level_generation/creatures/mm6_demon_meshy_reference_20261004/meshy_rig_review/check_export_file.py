import hashlib
import json
import struct
from pathlib import Path

import numpy as np

stage = Path(__file__).resolve().parent
source = Path('/home/pjasicek/Downloads/Meshy_AI_mm6_demon_cleaned_All_Animations.glb')

def read_glb(path):
    data = path.read_bytes()
    assert struct.unpack_from('<III', data) == (0x46546C67, 2, len(data))
    chunks = {}
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        chunks[kind] = data[offset:offset + length]
        offset += length
    gltf = json.loads(chunks[0x4E4F534A])
    raw = chunks[0x004E4942]

    def accessor(index):
        entry = gltf['accessors'][index]
        view = gltf['bufferViews'][entry['bufferView']]
        dtype = np.dtype({5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[entry['componentType']])
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[entry['type']]
        return np.ndarray((entry['count'], width), dtype=dtype, buffer=raw,
                          offset=view.get('byteOffset', 0) + entry.get('byteOffset', 0),
                          strides=(view.get('byteStride', dtype.itemsize * width), dtype.itemsize)).copy()
    return data, gltf, accessor

raw, gltf, access = read_glb(stage / 'mm6_demon_rig_corrected.glb')
assert len(gltf['meshes']) == len(gltf['skins']) == 1
assert len(gltf['meshes'][0]['primitives']) == 1
primitive = gltf['meshes'][0]['primitives'][0]
vertices = access(primitive['attributes']['POSITION'])
faces = access(primitive['indices']).reshape(-1, 3)
weights = np.concatenate([access(primitive['attributes'][name])
                          for name in ('WEIGHTS_0', 'WEIGHTS_1')], axis=1)
joints = np.concatenate([access(primitive['attributes'][name])
                         for name in ('JOINTS_0', 'JOINTS_1')], axis=1)
names = [gltf['nodes'][node]['name'] for node in gltf['skins'][0]['joints']]
assert len(vertices) == 7899 and len(faces) == 15686 and len(names) == 79
assert np.isfinite(vertices).all() and np.isfinite(weights).all()
assert np.max(np.abs(weights.sum(1) - 1)) < 1e-6
assert not gltf.get('materials') and not gltf.get('images') and 'TEXCOORD_0' not in primitive['attributes']
assert all(name in names for name in json.loads((stage / 'source.json').read_text())['audit']['joint_names'])
parents = {child: index for index, node in enumerate(gltf['nodes']) for child in node.get('children', [])}
node_ids = {node['name']: index for index, node in enumerate(gltf['nodes'])}
for bone, parent in [('Bone_041', 'mixamorig:LeftShoulder'), ('Bone_036', 'mixamorig:RightShoulder')]:
    assert parents[node_ids[bone]] == node_ids[parent], {'wrong_parent': bone}
toe_ids = [names.index(name) for name in names if name.endswith(('ToeBase', 'Toe_End'))]
assert not np.any(weights[np.isin(joints, toe_ids)] > 1e-8)
animations = [{'name': animation['name'],
               'start_seconds': min(float(access(s['input'])[0, 0]) for s in animation['samplers']),
               'duration_seconds': max(float(access(s['input'])[-1, 0]) for s in animation['samplers']),
               'channels': len(animation['channels']),
               'maximum_keys': max(len(access(s['input'])) for s in animation['samplers'])}
              for animation in gltf['animations']]
assert {record['name'] for record in animations} == {'Walking', 'Running'} and len(animations) == 2
for record in animations:
    expected = {'Walking': 25 / 24, 'Running': 16 / 24}[record['name']]
    assert abs(record['duration_seconds'] - expected) < 1e-6 and record['start_seconds'] == 0
original = np.load(stage / 'source_arrays.npz')
coordinate_error = float(np.max(np.abs(vertices - original['vertices'])))
order_identical = coordinate_error < 2e-6
if order_identical:
    assert np.array_equal(faces, original['faces']), 'Topology changed'
    assert coordinate_error < 2e-6
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'f7631fca2e11a01740035028b507584a6f1c4f2fd7251529918495b8bdaa9996'
report = {'file': 'mm6_demon_rig_corrected.glb', 'sha256': hashlib.sha256(raw).hexdigest(),
          'bytes': len(raw), 'vertices': len(vertices), 'triangles': len(faces), 'bones': len(names),
          'animations': animations, 'weight_sum_range': [float(weights.sum(1).min()), float(weights.sum(1).max())],
          'maximum_influences': int((weights > 1e-6).sum(1).max()),
          'direct_source_vertex_order_matches': order_identical,
          'direct_source_vertex_coordinate_error': coordinate_error,
          'source_sha256_unchanged': True, 'textures_or_uvs_added': False,
          'export_contains_only_corrected_mesh_and_rig': True}
(stage / 'export_file_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
