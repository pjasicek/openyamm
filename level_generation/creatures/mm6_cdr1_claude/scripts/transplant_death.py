"""Replace only the Death and Dead animations of the exported GLBs with work/death_clips.glb (animate_death.py),
matching channels by node name. Mesh, skin, texture and other clips' accessors stay byte-identical (checked), as do
the repairs applied to these exports after the master was first exported (teeth, ivory, scales)."""
import copy
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as rv

CLIPS = ('Death', 'Dead')


def accessor_data(doc, binary, index):
    meta = doc['accessors'][index]
    view = doc['bufferViews'][meta['bufferView']]
    start = view.get('byteOffset', 0) + meta.get('byteOffset', 0)
    return bytes(binary[start:start + view['byteLength'] - meta.get('byteOffset', 0)])


def append_accessor(doc, binary, meta, data):
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    meta = copy.deepcopy(meta)
    meta['bufferView'] = len(doc['bufferViews']) - 1
    meta.pop('byteOffset', None)
    doc['accessors'].append(meta)
    return len(doc['accessors']) - 1


def referenced_accessors(doc):
    used = set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            used.update(primitive['attributes'].values())
            if 'indices' in primitive:
                used.add(primitive['indices'])
            for target in primitive.get('targets', []):
                used.update(target.values())
    for skin in doc.get('skins', []):
        if 'inverseBindMatrices' in skin:
            used.add(skin['inverseBindMatrices'])
    for animation in doc.get('animations', []):
        for sampler in animation['samplers']:
            used.update((sampler['input'], sampler['output']))
    return used


def drop_unused_accessors(doc):
    used = sorted(referenced_accessors(doc))
    remap = {old: new for new, old in enumerate(used)}
    doc['accessors'] = [doc['accessors'][old] for old in used]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {k: remap[v] for k, v in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] = remap[primitive['indices']]
            if 'targets' in primitive:
                primitive['targets'] = [{k: remap[v] for k, v in t.items()} for t in primitive['targets']]
    for skin in doc.get('skins', []):
        if 'inverseBindMatrices' in skin:
            skin['inverseBindMatrices'] = remap[skin['inverseBindMatrices']]
    for animation in doc.get('animations', []):
        for sampler in animation['samplers']:
            sampler['input'], sampler['output'] = remap[sampler['input']], remap[sampler['output']]


def signature(doc, binary, keep):
    """Bytes of every mesh/skin accessor and every animation not being replaced, by stable keys."""
    result = {}
    for m, mesh in enumerate(doc['meshes']):
        for p, primitive in enumerate(mesh['primitives']):
            for name, index in primitive['attributes'].items():
                result[f'mesh{m}/{p}/{name}'] = accessor_data(doc, binary, index)
            result[f'mesh{m}/{p}/indices'] = accessor_data(doc, binary, primitive['indices'])
    for s, skin in enumerate(doc.get('skins', [])):
        result[f'skin{s}'] = accessor_data(doc, binary, skin['inverseBindMatrices'])
    for animation in doc.get('animations', []):
        if animation['name'] in keep:
            for c, channel in enumerate(animation['channels']):
                sampler = animation['samplers'][channel['sampler']]
                result[f"{animation['name']}/{c}"] = (accessor_data(doc, binary, sampler['input'])
                                                      + accessor_data(doc, binary, sampler['output']))
    return result


source, source_binary = rv.read_glb(P / 'work/death_clips.glb')
report = {}
for name in ['mm6_cdr1_selected.glb', 'mm6_cdr1_runtime_lod0.glb', 'mm6_cdr1_lods.glb', 'mm6_cdr1_shadow.glb']:
    doc, binary = rv.read_glb(P / 'export' / name)
    binary = bytearray(binary)
    others = [a['name'] for a in doc['animations'] if a['name'] not in CLIPS]
    before = signature(doc, binary, others)
    node_index = {node.get('name'): index for index, node in enumerate(doc['nodes'])}
    for clip in CLIPS:
        incoming = next(a for a in source['animations'] if a['name'] == clip)
        animation = {'name': clip, 'channels': [], 'samplers': []}
        for channel in incoming['channels']:
            target_name = source['nodes'][channel['target']['node']]['name']
            if target_name not in node_index:
                continue
            sampler = incoming['samplers'][channel['sampler']]
            animation['samplers'].append({
                'input': append_accessor(doc, binary, source['accessors'][sampler['input']],
                                         accessor_data(source, source_binary, sampler['input'])),
                'output': append_accessor(doc, binary, source['accessors'][sampler['output']],
                                          accessor_data(source, source_binary, sampler['output'])),
                'interpolation': sampler.get('interpolation', 'LINEAR')})
            animation['channels'].append({'sampler': len(animation['samplers']) - 1,
                                          'target': {'node': node_index[target_name],
                                                     'path': channel['target']['path']}})
        position = next(i for i, a in enumerate(doc['animations']) if a['name'] == clip)
        doc['animations'][position] = animation
    drop_unused_accessors(doc)
    doc, binary = rv._compact(doc, bytes(binary))
    assert signature(doc, binary, others) == before, name
    rv.write_glb(P / 'export' / name, doc, binary)
    report[name] = {'replaced': list(CLIPS), 'unchanged_animations': others, 'geometry_and_skin_identical': True}
(P / 'review/burn/transplant.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
