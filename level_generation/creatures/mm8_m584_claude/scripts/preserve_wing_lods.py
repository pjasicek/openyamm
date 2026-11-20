"""Keep thin feather coverage intact while reducing the humanoid and polearm LODs."""
import copy
import json
import sys
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import merge_shadow, accessor_bytes
from merge_head_material import read_glb, write_glb, accessor_array, append_accessor

path = P / 'export/raven_lods.glb'
d, b = read_glb(path)
b = bytearray(b)
original_document = copy.deepcopy(d)
original_binary = bytes(b)
base = next(i for i, m in enumerate(d['meshes']) if 'openyamm_lods' in m.get('extras', {}))
chain = [base] + d['meshes'][base]['extras']['openyamm_lods']
joint_names = [d['nodes'][i]['name'] for i in d['skins'][0]['joints']]
wing_joints = [i for i, name in enumerate(joint_names) if name.startswith(('Wing_', 'Feather_'))]


def wing_triangles(primitive):
    attributes = primitive['attributes']
    weight = np.zeros(d['accessors'][attributes['POSITION']]['count'])
    for name in attributes:
        if name.startswith('JOINTS_'):
            joints = accessor_array(d, b, attributes[name])
            weights = accessor_array(d, b, attributes['WEIGHTS_' + name[7:]])
            weight += (np.isin(joints, wing_joints) * weights).sum(axis=1)
    tri = accessor_array(d, b, primitive['indices']).reshape(-1, 3)
    wing = weight > .5
    assert np.all(wing[tri].all(axis=1) == wing[tri].any(axis=1))
    return tri[wing[tri].all(axis=1)], tri[~wing[tri].any(axis=1)]


body = next(p for p in d['meshes'][base]['primitives'] if d['materials'][p['material']]['name'] == 'Raven_A')
feathers, _ = wing_triangles(body)
assert len(feathers) == sum(row['triangles'] for row in json.loads((P / 'work/wings.json').read_text()))
wing = copy.deepcopy(body)
wing['indices'] = append_accessor(d, b, feathers.ravel().astype(np.uint32),
                                  {'componentType': 5125, 'type': 'SCALAR'}, 34963)
for mesh_index in chain[1:]:
    mesh = d['meshes'][mesh_index]
    for i, primitive in enumerate(mesh['primitives']):
        if primitive['material'] != body['material']:
            continue
        _, retained = wing_triangles(primitive)
        reduced = copy.deepcopy(primitive)
        reduced['indices'] = append_accessor(d, b, retained.ravel().astype(np.uint32),
                                             {'componentType': 5125, 'type': 'SCALAR'}, 34963)
        merged = merge_shadow(d, b, {'name': mesh['name'], 'primitives': [reduced, wing]})
        mesh['primitives'][i] = merged['primitives'][0]
for mesh_index, shadow_index in zip(chain, d['meshes'][base]['extras']['openyamm_shadow_lods']):
    d['meshes'][shadow_index] = merge_shadow(d, b, d['meshes'][mesh_index])
# LOD0, skin and animation samples remain the reviewed revision.
assert d['meshes'][base] == original_document['meshes'][base]
assert d['animations'] == original_document['animations'] and d['skins'] == original_document['skins']
for i in range(len(original_document['accessors'])):
    assert accessor_bytes(d, b, i) == accessor_bytes(original_document, original_binary, i)
write_glb(path, d, b)
counts = [sum(d['accessors'][p['indices']]['count'] // 3 for p in d['meshes'][i]['primitives']) for i in chain]
assert all(a > c for a, c in zip(counts, counts[1:]))
report = json.loads((P / 'export/lods.json').read_text())
report.update(triangles=counts, feather_triangles_per_level=len(feathers),
              deviation='Thin feather shells retain full coverage at every LOD; humanoid and polearm still reduce.',
              lod0_skin_animation_accessors_preserved=True)
(P / 'export/lods.json').write_text(json.dumps(report, indent=2) + '\n')
print(report)
