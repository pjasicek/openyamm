"""Append casting channels/sockets without re-exporting selected geometry, textures, LODs or native clips."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import shutil

stage = Path(__file__).resolve().parent
sys.path.insert(0, str(stage.parents[3] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor


def merge(source, destination):
    before, original = read_glb(source)
    exported, payload = read_glb(stage / 'cast_export.glb')
    document = copy.deepcopy(before)
    binary = bytearray(original)
    indices = {n['name']: i for i, n in enumerate(document['nodes']) if 'name' in n}
    clip = copy.deepcopy(next(a for a in exported['animations'] if a['name'] == 'Cast_FireBolt'))
    assert not any(a['name'] == clip['name'] for a in document['animations'])
    for channel in clip['channels']:
        node = exported['nodes'][channel['target']['node']]
        target = document['nodes'][indices[node['name']]]
        # Bone-local channels require the exact same bind basis, not just identical node names.
        for prop, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
            assert max(abs(a-b) for a, b in zip(node.get(prop, default), target.get(prop, default))) < 2e-6, (
                node['name'], prop, node.get(prop), target.get(prop))
        channel['target']['node'] = indices[node['name']]
    for sampler in clip['samplers']:
        for prop in ('input', 'output'):
            index = sampler[prop]
            sampler[prop] = append_accessor(document, binary, exported['accessors'][index],
                                             accessor_bytes(exported, payload, index))
    # The selected asset owns explicit body/effect visibility tracks. Casting inherits Standing's held values.
    # Missing visibility keys would reset the body parent to its hidden rest scale.
    standing = next(a for a in before['animations'] if a['name'] == 'Standing')
    animated = {(c['target']['node'], c['target']['path']) for c in clip['channels']}
    for channel in standing['channels']:
        target = channel['target']
        if document['nodes'][target['node']].get('name') not in (
                'Demon_Body_Visibility', 'Demon_Ash_Remains', 'Demon_Death_Plume'):
            continue
        if (target['node'], target['path']) not in animated:
            copied = copy.deepcopy(channel)
            copied['sampler'] = len(clip['samplers'])
            clip['samplers'].append(copy.deepcopy(standing['samplers'][channel['sampler']]))
            clip['channels'].append(copied)
    document['animations'].append(clip)
    sockets = {}
    for i, node in enumerate(exported['nodes']):
        if not node.get('name', '').startswith('Socket_'):
            continue
        parent = next(n for n in exported['nodes'] if i in n.get('children', []))
        target_parent = document['nodes'][indices[parent['name']]]
        target_parent.setdefault('children', []).append(len(document['nodes']))
        document['nodes'].append(copy.deepcopy(node))
        sockets[node['name']] = parent['name']
    assert len(sockets) == 4
    # Shared payload references and all originals stay intact. This also protects merged shadow meshes and LOD extras.
    assert document['meshes'] == before['meshes']
    assert document['skins'] == before['skins']
    assert document['materials'] == before['materials'] and document['images'] == before['images']
    assert document['animations'][:-1] == before['animations']
    assert bytes(binary[:len(original)]) == original
    write_glb(destination, document, bytes(binary))
    return {'source': str(source), 'destination': str(destination),
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'socket_parents': sockets, 'original_binary_prefix_preserved': True,
            'original_clip_count': len(before['animations']), 'new_clip': clip['name'],
            'skin_joint_counts': [len(s['joints']) for s in document['skins']]}


if __name__ == '__main__':
    reports = []
    baseline = stage / 'runtime_before.glb'
    if not baseline.exists():
        shutil.copy2(stage.parents[3] / 'assets_dev/worlds/mm6/models/mm6_demon.glb', baseline)
    for source, destination in [
        (stage.parent / 'texturing_fixed_20261005/mm6_demon_textured.glb', stage / 'mm6_demon_animated.glb'),
        (baseline, stage / 'mm6_demon_runtime.glb')]:
        reports.append(merge(source, destination))
    (stage / 'export_checks.json').write_text(json.dumps(reports, indent=2) + '\n')
    print('Preserved original meshes/materials/skins/clips and appended Cast_FireBolt + four socket nodes.')
