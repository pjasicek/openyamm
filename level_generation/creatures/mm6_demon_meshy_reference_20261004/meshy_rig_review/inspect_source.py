import hashlib
import json
import struct
from pathlib import Path

import numpy as np

stage = Path(__file__).resolve().parent
source = Path('/home/pjasicek/Downloads/Meshy_AI_mm6_demon_cleaned_All_Animations.glb')
data = source.read_bytes()
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
    dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[entry['componentType']]
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[entry['type']]
    result = np.frombuffer(raw, dtype, count=entry['count'] * width,
                          offset=view.get('byteOffset', 0) + entry.get('byteOffset', 0))
    return result.reshape(entry['count'], width)

primitive = gltf['meshes'][0]['primitives'][0]
vertices = accessor(primitive['attributes']['POSITION'])
faces = accessor(primitive['indices']).reshape(-1, 3)
weights = np.concatenate([accessor(primitive['attributes'][key])
                          for key in ('WEIGHTS_0', 'WEIGHTS_1')], axis=1)
joints = np.concatenate([accessor(primitive['attributes'][key])
                         for key in ('JOINTS_0', 'JOINTS_1')], axis=1)
names = [gltf['nodes'][node]['name'] for node in gltf['skins'][0]['joints']]
regions = {'shoulder_spikes': (np.abs(vertices[:, 0]) > .35) & (vertices[:, 1] > 1.4),
           'feet': vertices[:, 1] < .14}
report = {'source': str(source), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
          'vertices': len(vertices), 'triangles': len(faces), 'bounds': [vertices.min(0).tolist(), vertices.max(0).tolist()],
          'joint_count': len(names), 'joint_names': names,
          'animations': [{'name': animation['name'],
                          'seconds': max(float(accessor(sampler['input'])[-1, 0]) for sampler in animation['samplers']),
                          'channels': len(animation['channels'])} for animation in gltf['animations']],
          'weight_sum_range': [float(weights.sum(1).min()), float(weights.sum(1).max())],
          'max_influences': int((weights > 1e-6).sum(1).max()),
          'materials': len(gltf.get('materials', [])), 'uvs': 'TEXCOORD_0' in primitive['attributes'],
          'region_weight_totals': {}}
for label, selected in regions.items():
    totals = np.zeros(len(names))
    for ids, values in zip(joints[selected], weights[selected]):
        np.add.at(totals, ids, values)
    report['region_weight_totals'][label] = {names[index]: round(float(totals[index]), 3)
        for index in np.argsort(-totals) if totals[index] > .1}
(stage / 'source.json').write_text(json.dumps({'audit': report, 'gltf': gltf}, indent=2) + '\n')
np.savez(stage / 'source_arrays.npz', vertices=vertices, faces=faces, joints=joints, weights=weights)
print(json.dumps(report, indent=2))
