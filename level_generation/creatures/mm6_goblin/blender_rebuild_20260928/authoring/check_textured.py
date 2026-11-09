"""Verify the revised attack and exact preservation of geometry, materials and the other six actions."""
import hashlib
import json

from check_glb import Glb, ROOT


def channels(glb):
    result = {}
    for action in glb.json['animations']:
        for channel in action['channels']:
            target = channel['target']
            sampler = action['samplers'][channel['sampler']]
            key = (action['name'], glb.json['nodes'][target['node']]['name'], target['path'])
            result[key] = (glb.accessor(sampler['input']), glb.accessor(sampler['output']),
                           sampler.get('interpolation', 'LINEAR'))
    return result


def image_bytes(glb, image):
    view = glb.json['bufferViews'][image['bufferView']]
    offset = view.get('byteOffset', 0)
    return glb.binary[offset:offset + view['byteLength']]


def check():
    """Prove that this revision changes only the attack animation."""
    baseline = ROOT / 'review/attack_elbow_correction/before/delivery/mm6_goblin_textured_rigged.glb'
    source = ROOT / 'delivery/mm6_goblin_textured_rigged.glb'
    old, new = Glb(baseline), Glb(source)
    report = new.audit(True)
    assert old.surfaces() == new.surfaces(), 'Bind surfaces, topology or UVs changed.'
    def payload(glb):
        return {node['name']: [{'indices': glb.accessor(primitive['indices']),
                               'attributes': {name: glb.accessor(index)
                                              for name, index in primitive['attributes'].items()},
                               'material': primitive['material']}
                              for primitive in glb.json['meshes'][node['mesh']]['primitives']]
                for node in glb.json['nodes'] if 'mesh' in node}
    assert payload(old) == payload(new), 'Mesh attributes, weights or material assignments changed.'
    assert old.json['materials'] == new.json['materials'], 'Materials changed.'
    old_maps = {hashlib.sha256(image_bytes(old, image)).hexdigest() for image in old.json['images']}
    new_maps = {hashlib.sha256(image_bytes(new, image)).hexdigest() for image in new.json['images']}
    assert old_maps == new_maps, 'Packed texture images changed.'
    for a, b in zip(old.json['skins'], new.json['skins']):
        assert [old.json['nodes'][i]['name'] for i in a['joints']] == [new.json['nodes'][i]['name'] for i in b['joints']]
        assert old.accessor(a['inverseBindMatrices']) == new.accessor(b['inverseBindMatrices'])
    before, after = channels(old), channels(new)
    assert before.keys() == after.keys(), 'Clip/channel inventory changed.'
    changed = [key for key in before if before[key] != after[key]]
    assert changed and all(key[0] == 'attack' for key in changed), 'An animation other than attack changed.'
    assert {key[1] for key in changed}.issuperset({'upper_arm.R', 'forearm.R', 'upper_arm.L', 'forearm.L'})
    for key, (times, values, interpolation) in after.items():
        if key[0] == 'attack' and key[2] == 'scale':
            assert all(abs(value - 1) < .00002 for row in values for value in row), (key, 'Scaled bone')
    report.update(status='pass', revision='attack_elbow_8', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                  only_changed_animation='attack', unchanged_clips=sorted({key[0] for key in before} - {'attack'}),
                  changed_attack_channels=[list(key) for key in changed],
                  all_bind_surfaces_topology_uvs_normals_weights_identical=True,
                  joint_order_and_inverse_bind_matrices_identical=True,
                  all_materials_and_packed_images_identical=True, attack_bone_scales_are_unit=True)
    (ROOT / 'delivery/textured_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Textured export passes: only attack changed; geometry, maps, rig and six other clips are identical.')


if __name__ == '__main__':
    check()
