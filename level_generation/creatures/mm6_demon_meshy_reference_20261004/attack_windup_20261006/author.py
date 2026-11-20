"""Raise the existing attack windup through one upper-arm rotation channel."""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Matrix, Quaternion

stage = Path(__file__).resolve().parent
repo = stage.parents[3]
sys.path.insert(0, str(repo / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor

previous = stage.parent / 'animation_controller_20261006'
bpy.ops.wm.open_mainfile(filepath=str(previous / 'mm6_demon_animation_master.blend'))
scene = bpy.context.scene
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
track = next(t for t in rig.animation_data.nla_tracks if t.name == 'Attack')
baseline = track.strips[0].action
action = baseline.copy()
action.name = 'Demon_Attack_Higher_Windup'
for other in rig.animation_data.nla_tracks:
    other.mute = True
rig.animation_data.action = baseline
rig.animation_data.action_slot = baseline.slots[0]
bone_name = 'mixamorig:RightArm'
path = f'pose.bones["{bone_name}"].rotation_quaternion'
rotations = []
report = {'peak_extra_degrees': 24, 'peak_frame': 12, 'fps': 48, 'duration_seconds': .75, 'poses': []}


def amount(frame):
    if frame <= 12:
        t = frame / 12
    else:
        t = max(0, (18 - frame) / 6)
    return t * t * (3 - 2 * t)


for frame in range(37):
    scene.frame_set(frame)
    bone = rig.pose.bones[bone_name]
    before = rig.pose.bones['mixamorig:RightHand'].head.copy()
    pivot = bone.head.copy()
    rotation = Quaternion((0, 1, 0), math.radians(24 * amount(frame)))
    bone.matrix = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ bone.matrix
    bpy.context.view_layer.update()
    quaternion = bone.rotation_quaternion.copy()
    if rotations and quaternion.dot(rotations[-1]) < 0:
        quaternion.negate()
    rotations.append(quaternion)
    if frame in (0, 6, 12, 18, 24, 30, 36):
        after = rig.pose.bones['mixamorig:RightHand'].head
        report['poses'].append({'frame': frame, 'wrist_before': list(before), 'wrist_after': list(after)})

curves = action.layers[0].strips[0].channelbag(action.slots[0]).fcurves
for curve in curves:
    if curve.data_path == path:
        assert len(curve.keyframe_points) == 37
        for frame, key in enumerate(curve.keyframe_points):
            assert abs(key.co.x - frame) < 1e-6
            key.co.y = rotations[frame][curve.array_index]
            key.interpolation = 'LINEAR'
        curve.update()

original_curves = baseline.layers[0].strips[0].channelbag(baseline.slots[0]).fcurves
for original, changed in zip(original_curves, curves):
    assert original.data_path == changed.data_path and original.array_index == changed.array_index
    if original.data_path != path:
        assert [list(k.co) for k in original.keyframe_points] == [list(k.co) for k in changed.keyframe_points]
    else:
        for frame in (0, 18, 24, 30, 36):
            assert abs(original.keyframe_points[frame].co.y - changed.keyframe_points[frame].co.y) < 2e-6

rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.frame_set(12)
for obj in scene.objects:
    obj.select_set(obj == rig or obj.get('material_role') == 'body' or obj.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(stage / 'attack_export.glb'), export_format='GLB', use_selection=True,
    use_active_scene=True, export_animations=True, export_animation_mode='ACTIVE_ACTIONS',
    export_frame_range=False, export_force_sampling=True, export_all_influences=True,
    export_def_bones=False, export_optimize_animation_size=False, export_extras=True,
    export_cameras=False, export_lights=False)
rig.animation_data.action = None
track.strips[0].action = action
track.strips[0].action_slot = action.slots[0]
track.mute = False
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_animation_master.blend'), compress=True)

exported, payload = read_glb(stage / 'attack_export.glb')
channels = [(clip, channel) for clip in exported['animations'] for channel in clip['channels']
            if exported['nodes'][channel['target']['node']].get('name') == bone_name
            and channel['target']['path'] == 'rotation']
assert len(channels) == 1, [(clip['name'], channel) for clip, channel in channels]
export_clip, export_channel = channels[0]
sampler = export_clip['samplers'][export_channel['sampler']]
new_rotation = exported['accessors'][sampler['output']]
new_times = accessor_bytes(exported, payload, sampler['input'])
new_keys = accessor_bytes(exported, payload, sampler['output'])


def merge(source, destination):
    before, original = read_glb(source)
    document = copy.deepcopy(before)
    binary = bytearray(original)
    clip = next(a for a in document['animations'] if a['name'] == 'Attack')
    channel = next(c for c in clip['channels'] if document['nodes'][c['target']['node']].get('name') == bone_name
                   and c['target']['path'] == 'rotation')
    target_node = document['nodes'][channel['target']['node']]
    exported_node = exported['nodes'][export_channel['target']['node']]
    for prop, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
        assert max(abs(a - b) for a, b in zip(target_node.get(prop, default),
                                             exported_node.get(prop, default))) < 2e-6, prop
    target_sampler = clip['samplers'][channel['sampler']]
    old_times = accessor_bytes(document, binary, target_sampler['input'])
    assert len(old_times) == len(new_times)
    assert max(abs(a[0] - b[0]) for a, b in zip(struct.iter_unpack('<f', old_times),
                                               struct.iter_unpack('<f', new_times))) < 1e-7
    old_keys = accessor_bytes(document, binary, target_sampler['output'])
    old_quaternions = list(struct.iter_unpack('<4f', old_keys))
    new_quaternions = list(struct.iter_unpack('<4f', new_keys))
    for frame in (0, *range(18, 37)):
        a, b = old_quaternions[frame], new_quaternions[frame]
        assert min(max(abs(x - y) for x, y in zip(a, b)), max(abs(x + y) for x, y in zip(a, b))) < 2e-6
    target_sampler['output'] = append_accessor(document, binary, new_rotation, new_keys)
    for prop in ('nodes', 'meshes', 'skins', 'materials', 'images'):
        assert document[prop] == before[prop], prop
    for original_clip, updated_clip in zip(before['animations'], document['animations']):
        if original_clip['name'] != 'Attack':
            assert original_clip == updated_clip
    assert bytes(binary[:len(original)]) == original
    write_glb(destination, document, bytes(binary))
    return {'source': str(source), 'destination': str(destination),
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'changed_clip': 'Attack', 'changed_channel': bone_name + '.rotation',
            'original_binary_prefix_preserved': True, 'key_times_preserved': True,
            'other_clips_and_asset_data_preserved': True}


runtime = stage / 'runtime_before.glb'
if not runtime.exists():
    runtime = repo / 'assets_dev/worlds/mm6/models/mm6_demon.glb'
assert hashlib.sha256(runtime.read_bytes()).hexdigest() == \
    'a9ca886b6725a8ccb88ff58623e60681e04a0fda43b84f24e52802cea3f43dca', 'Selected runtime revision changed'
report['exports'] = [merge(previous / 'mm6_demon_animated.glb', stage / 'mm6_demon_animated.glb'),
                     merge(runtime, stage / 'mm6_demon_runtime.glb')]
peak = next(p for p in report['poses'] if p['frame'] == 12)
assert peak['wrist_after'][2] > peak['wrist_before'][2] + .18
(stage / 'export_checks.json').write_text(json.dumps(report, indent=2) + '\n')
print('Prepared higher windup; original meshes, LODs, other clips and all key times preserved.', flush=True)
