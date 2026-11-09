"""The opening revision must change only Attack animation data in the portable model."""
import hashlib
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from merge_head_material import read_glb
from build_actor_lods import accessor_bytes


def mesh_data(doc, binary):
    return [[(accessor_bytes(doc, binary, primitive['indices']),
              {name: accessor_bytes(doc, binary, index) for name, index in primitive['attributes'].items()})
             for primitive in mesh['primitives']] for mesh in doc['meshes']]


def animations(doc, binary):
    return {a['name']: {(doc['nodes'][c['target']['node']]['name'], c['target']['path']):
            tuple(accessor_bytes(doc, binary, a['samplers'][c['sampler']][key]) for key in ['input', 'output'])
            for c in a['channels']} for a in doc['animations']}


def images(doc, binary):
    result = []
    for image in doc['images']:
        view = doc['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        result.append(bytes(binary[start:start + view['byteLength']]))
    return result


before, bb = read_glb(P / 'work/attack_opening_v2/mm8_m628.glb')
after, ab = read_glb(P / 'export/mm8_m628.glb')
assert mesh_data(before, bb) == mesh_data(after, ab), 'Geometry/UV/weights changed'
assert images(before, bb) == images(after, ab), 'Textures changed'
assert before['nodes'] == after['nodes'], 'Node transforms changed'
assert before['materials'] == after['materials'], 'Materials changed'
old, new = animations(before, bb), animations(after, ab)
assert old['Attack'] != new['Attack'], 'Attack was not updated'
assert {n: a for n, a in old.items() if n != 'Attack'} == {n: a for n, a in new.items() if n != 'Attack'}
report = {'changed_clips': ['Attack'], 'geometry_uv_weights_unchanged': True, 'textures_unchanged': True,
          'nodes_materials_unchanged': True, 'other_clips_byte_identical': True,
          'sha256': hashlib.sha256((P / 'export/mm8_m628.glb').read_bytes()).hexdigest()}
(P / 'work/attack_opening_export_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
