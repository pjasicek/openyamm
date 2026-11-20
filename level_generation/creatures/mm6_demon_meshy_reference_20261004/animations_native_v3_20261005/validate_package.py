"""Check delivered geometry, deformation, retained actions and actual GLB round-trip."""
import bpy
import hashlib
import importlib.util
import json
import numpy as np
import struct
from pathlib import Path

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage/'mm6_demon_native_animations.blend'))
spec = importlib.util.spec_from_file_location('motion', stage/'motion.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
source, rig, mesh = motion.objects()
rig.hide_set(False)
with bpy.data.libraries.load(str(stage.parent/'animations_native_v2_20261005/mm6_demon_native_animations.blend')) as (available, loaded):
    loaded.scenes = ['MM6_Demon_Native_Animations']
baseline = loaded.scenes[0]
old_rig = next(o for o in baseline.objects if o.type == 'ARMATURE')
old_mesh = next(o for o in baseline.objects if o.type == 'MESH')


def rest_vertices(m):
    a = np.empty(len(m.data.vertices)*3, np.float32)
    m.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def evaluated_vertices(scene, obj):
    bpy.context.window.scene = scene
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    a = np.empty(len(temporary.vertices)*3, np.float32)
    temporary.vertices.foreach_get('co', a)
    matrix = np.array(evaluated.matrix_world)
    evaluated.to_mesh_clear()
    return a.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def select(scene, clip, frame):
    bpy.context.window.scene = scene
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            obj.hide_set(False)
        for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
            if owner is not None and owner.animation_data:
                matching = [t.strips[0] for t in owner.animation_data.nla_tracks if t.name == clip]
                for track in owner.animation_data.nla_tracks:
                    track.mute = True
                owner.animation_data.action = matching[0].action if matching else None
                if matching:
                    owner.animation_data.action_slot = matching[0].action_slot
    scene.frame_set(int(frame), subframe=float(frame%1))
    bpy.context.view_layer.update()


def curves(action):
    return {(c.data_path, c.array_index): [(tuple(k.co), k.interpolation) for k in c.keyframe_points]
            for c in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves}


assert np.array_equal(rest_vertices(mesh), rest_vertices(old_mesh))
assert [tuple(p.vertices) for p in mesh.data.polygons] == [tuple(p.vertices) for p in old_mesh.data.polygons]
assert [g.name for g in mesh.vertex_groups] == [g.name for g in old_mesh.vertex_groups]
assert [[(g.group, g.weight) for g in v.groups] for v in mesh.data.vertices] == [
       [(g.group, g.weight) for g in v.groups] for v in old_mesh.data.vertices]
for b in rig.data.bones:
    assert np.array_equal(np.array(b.matrix_local), np.array(old_rig.data.bones[b.name].matrix_local)), b.name
retained = {}
for clip, end in {**motion.ENDS, 'Walking': 50, 'Running': 32}.items():
    a = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name == clip)
    b = next(t.strips[0].action for t in old_rig.animation_data.nla_tracks if t.name == clip)
    assert curves(a) == curves(b), clip
    maximum = 0
    for time in np.arange(0, end+.01, .5):
        select(source, clip, float(time))
        expected = evaluated_vertices(source, mesh)
        select(baseline, clip, float(time))
        actual = evaluated_vertices(baseline, old_mesh)
        maximum = max(maximum, float(np.abs(expected-actual).max()))
    assert maximum < 1e-7, (clip, maximum)
    retained[clip] = {'identical_curves': True, 'samples': int(end*2+1), 'maximum_world_vertex_change': maximum}
print('Preserved baseline mesh, bind, weights and all eight other actions.', flush=True)

# Attack changes only the requested right arm/hand rotations. Its feet, left arm and body remain exact.
spec = importlib.util.spec_from_file_location('revise_attack', stage/'revise_attack.py')
revision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revision)
new_attack = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name == 'Attack')
old_attack = next(t.strips[0].action for t in old_rig.animation_data.nla_tracks if t.name == 'Attack')
new_curves, old_curves = curves(new_attack), curves(old_attack)
allowed = {f'pose.bones["{name}"].rotation_quaternion' for name in revision.CHANGED_BONES}
assert {k:v for k,v in new_curves.items() if k[0] not in allowed} == {
       k:v for k,v in old_curves.items() if k[0] not in allowed}
attack_scope = dict(changed_bones=revision.CHANGED_BONES, all_other_channels_identical=True)
right_tips = [i for name, indices in motion.TIP_MASKS.items() if name.startswith('Right_') for i in indices]
select(source, 'Attack', 12)
corrected = evaluated_vertices(source, mesh)[right_tips]
corrected_wrist = tuple(rig.pose.bones['mixamorig:RightHand'].head)
select(baseline, 'Attack', 12)
previous = evaluated_vertices(baseline, old_mesh)[right_tips]
previous_wrist = tuple(old_rig.pose.bones['mixamorig:RightHand'].head)
attack_scope['C_tip_bounds_before'] = dict(minimum_x=float(previous[:, 0].min()), maximum_z=float(previous[:, 2].max()))
attack_scope['C_tip_bounds_after'] = dict(minimum_x=float(corrected[:, 0].min()), maximum_z=float(corrected[:, 2].max()))
attack_scope['C_wrist_before'], attack_scope['C_wrist_after'] = previous_wrist, corrected_wrist
assert corrected[:, 0].min() < previous[:, 0].min()-.04
assert corrected[:, 2].max() > previous[:, 2].max()+.07
assert corrected_wrist[2] > previous_wrist[2]+.04

data = motion.SOURCE
rest, faces, weights, names = data['vertices'], data['faces'], data['weights'], list(data['group_names'])
edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
lengths = np.linalg.norm(rest[edges[:, 0]]-rest[edges[:, 1]], axis=1)
areas = np.linalg.norm(np.cross(rest[faces[:, 1]]-rest[faces[:, 0]], rest[faces[:, 2]]-rest[faces[:, 0]]), axis=1)
feet = {s: weights[:, names.index('mixamorig:'+s+'Foot')] > .999 for s in ('Right', 'Left')}
foot_edges = {s: np.all(mask[edges], axis=1) for s, mask in feet.items()}
tip_edges = []
for indices in motion.TIP_MASKS.values():
    mask = np.zeros(len(rest), bool)
    mask[indices] = True
    tip_edges.append(np.all(mask[edges], axis=1))
tip_edges = np.any(tip_edges, axis=0)
deformation = {}
for clip, end in {**motion.ENDS, 'Attack': 36}.items():
    if clip == 'Ash_Remains':
        continue
    stats = dict(samples=0, minimum_sole_height=100., maximum_rigid_foot_edge_error=0.,
                 maximum_hard_claw_edge_error=0., minimum_triangle_area_ratio=100.,
                 minimum_tail_distance_from_root_tip_line=100., maximum_bone_scale_error=0.,
                 maximum_non_root_translation=0., maximum_hard_claw_edge_absolute_error=0., worst_face=None)
    key_arrays = []
    for time in np.arange(0, (18 if clip == 'Death' else end)+.001, .25):
        if clip == 'Death' and time >= 18:
            continue
        select(source, clip, float(time))
        v = evaluated_vertices(source, mesh)
        ratios = np.linalg.norm(v[edges[:, 0]]-v[edges[:, 1]], axis=1)/lengths
        area = np.linalg.norm(np.cross(v[faces[:, 1]]-v[faces[:, 0]], v[faces[:, 2]]-v[faces[:, 0]]), axis=1)/areas
        if float(area.min()) < stats['minimum_triangle_area_ratio']:
            stats['minimum_triangle_area_ratio'] = float(area.min())
            fi = int(area.argmin())
            stats['worst_face'] = dict(frame=float(time), index=fi, vertices=faces[fi].tolist(),
                                      groups=[[(names[i], float(w)) for i, w in enumerate(weights[vi]) if w > .01]
                                              for vi in faces[fi]])
        stats['maximum_hard_claw_edge_error'] = max(stats['maximum_hard_claw_edge_error'], float(np.abs(ratios[tip_edges]-1).max()))
        stats['maximum_hard_claw_edge_absolute_error'] = max(stats['maximum_hard_claw_edge_absolute_error'],
                float((np.abs(ratios-1)*lengths)[tip_edges].max()))
        for side in feet:
            stats['minimum_sole_height'] = min(stats['minimum_sole_height'], float(v[feet[side], 2].min()))
            stats['maximum_rigid_foot_edge_error'] = max(stats['maximum_rigid_foot_edge_error'],
                                                       float(np.abs(ratios[foot_edges[side]]-1).max()))
        tail = np.array([tuple(rig.pose.bones[f'Bone_{i:03d}'].head) for i in range(20, 14, -1)])
        tail = np.vstack([tail, np.array(rig.pose.bones['Bone_015'].tail)])
        axis = tail[-1]-tail[0]
        axis /= np.linalg.norm(axis)
        delta = tail-tail[0]
        distance = np.linalg.norm(delta-np.outer(delta@axis, axis), axis=1).max()
        stats['minimum_tail_distance_from_root_tip_line'] = min(stats['minimum_tail_distance_from_root_tip_line'], float(distance))
        stats['maximum_bone_scale_error'] = max(stats['maximum_bone_scale_error'],
                                                max(max(abs(s-1) for s in b.scale) for b in rig.pose.bones))
        stats['maximum_non_root_translation'] = max(stats['maximum_non_root_translation'],
                                                    max(b.location.length for b in rig.pose.bones if b.name != 'mixamorig:Hips'))
        if time.is_integer():
            key_arrays.append(v)
        stats['samples'] += 1
    assert stats['minimum_sole_height'] > 0, (clip, stats)
    assert stats['maximum_rigid_foot_edge_error'] < 1e-4, (clip, stats)
    assert stats['maximum_hard_claw_edge_absolute_error'] < 1e-6, (clip, stats)
    assert stats['minimum_triangle_area_ratio'] > .02, (clip, stats)
    # A 10 cm deviation from the root-tip chord is visibly curved on this 1.8 m body.
    if clip != 'Attack':
        assert stats['minimum_tail_distance_from_root_tip_line'] > .10, (clip, stats)
    assert stats['maximum_bone_scale_error'] < 1e-7 and stats['maximum_non_root_translation'] < 1e-7
    if clip == 'Walk_Native':
        stats['loop_vertex_error'] = float(np.abs(key_arrays[0]-key_arrays[-1]).max())
        assert stats['loop_vertex_error'] < 1e-5
    deformation[clip] = stats
    print('Deformation', clip, stats, flush=True)

raw = (stage/'mm6_demon_native_animations.glb').read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
gltf = json.loads(raw[20:20+size])
binary = raw[28+size:]
assert len(gltf['skins'][0]['joints']) == 85 and len(gltf['meshes']) == 3
assert not gltf.get('textures') and not gltf.get('cameras')


def accessor(index):
    item = gltf['accessors'][index]
    view = gltf['bufferViews'][item['bufferView']]
    components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[item['type']]
    return np.frombuffer(binary, '<f4', count=item['count']*components,
                         offset=view.get('byteOffset', 0)+item.get('byteOffset', 0))


durations = {}
for animation in gltf['animations']:
    end = {**motion.ENDS, 'Attack': 36, 'Walking': 50, 'Running': 32}[animation['name']]
    duration = max(float(accessor(s['input']).max()) for s in animation['samplers'])
    assert abs(duration-end/48) < 1e-6
    durations[animation['name']] = duration
    channels = {gltf['nodes'][c['target']['node']]['name']+'_'+c['target']['path']: c for c in animation['channels']}
    for name in ('Demon_Body_Visibility_scale', 'Demon_Ash_Remains_scale'):
        assert animation['samplers'][channels[name]['sampler']]['interpolation'] == 'STEP'
    channel = channels['Demon_Death_Plume_weights']
    if animation['name'] != 'Death':
        assert not accessor(animation['samplers'][channel['sampler']]['output']).any()

target = bpy.data.scenes.new('Actual_Export_Check')
target.render.fps = 48
bpy.context.window.scene = target
bpy.ops.import_scene.gltf(filepath=str(stage/'mm6_demon_native_animations.glb'))
# Blender appends .001 because the source project is still loaded. Match the imported-scene identities.
target_objects = {name: next(o for o in target.objects if o.name.partition('.')[0] == name)
                  for name in ('Demon_Native_Mesh', 'Demon_Death_Plume', 'Demon_Body_Visibility', 'Demon_Ash_Remains')}
target_mesh = target_objects['Demon_Native_Mesh']
target_rig = next(o for o in target.objects if o.type == 'ARMATURE')
assert len(target_rig.data.bones) == 85
assert len(target_mesh.data.vertices) == 7899 and len(target_mesh.data.polygons) == 15686
assert [tuple(p.vertices) for p in target_mesh.data.polygons] == [tuple(p.vertices) for p in mesh.data.polygons]
rest_error = float(np.abs(rest_vertices(mesh)-rest_vertices(target_mesh)).max())
assert rest_error < 1e-5
roundtrip = {}
for clip, end in {**motion.ENDS, 'Attack': 36, 'Walking': 50, 'Running': 32}.items():
    maximum, scale_error, morph_error = 0, 0, 0
    for time in np.arange(0, end+.001, .25):
        select(source, clip, float(time))
        expected = evaluated_vertices(source, mesh)
        scales = {name: np.array(source.objects[name].scale) for name in ('Demon_Body_Visibility', 'Demon_Ash_Remains')}
        morph = np.array([k.value for k in source.objects['Demon_Death_Plume'].data.shape_keys.key_blocks][1:])
        select(target, clip, float(time))
        actual = evaluated_vertices(target, target_mesh)
        error = float(np.abs(expected-actual).max())
        maximum = max(maximum, error)
        scale_error = max(scale_error, *(float(np.abs(np.array(target_objects[n].scale)-v).max()) for n, v in scales.items()))
        target_morph = np.array([k.value for k in target_objects['Demon_Death_Plume'].data.shape_keys.key_blocks][1:])
        morph_error = max(morph_error, float(np.abs(morph-target_morph).max()))
    assert maximum < 1e-5 and scale_error < 1e-6 and morph_error < 1e-5, (clip, maximum, scale_error, morph_error)
    roundtrip[clip] = dict(samples=end*4+1, maximum_body_vertex_error=maximum,
                           maximum_visibility_error=scale_error, maximum_morph_weight_error=morph_error)
    print('Roundtrip', clip, roundtrip[clip], flush=True)

# Exercise state resets explicitly in one imported scene, including a return from Death/Ash.
switches = []
for clip, frame in [('Death', 30), ('Ash_Remains', 6), ('Walk_Native', 15), ('Hit', 18), ('Standing', 0)]:
    select(target, clip, frame)
    body_scale = tuple(target_objects['Demon_Body_Visibility'].scale)
    ash_scale = tuple(target_objects['Demon_Ash_Remains'].scale)
    assert body_scale == ((0.,)*3 if clip in ('Death', 'Ash_Remains') else (1.,)*3)
    assert ash_scale == ((1.,)*3 if clip == 'Ash_Remains' else (0.,)*3)
    switches.append(dict(clip=clip, frame=frame, body_scale=body_scale, ash_scale=ash_scale))
report = dict(actual_glb_reimport=True, vertices=7899, triangles=15686, joints=85,
              geometry_bind_weights_exactly_preserved=True, retained_clips=retained,
              revised_attack_scope=attack_scope,
              deformation=deformation, clip_durations_seconds=durations, roundtrip=roundtrip,
              imported_rest_coordinate_error=rest_error, clip_switches=switches,
              baseline_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [stage.parent/'animations_native_v2_20261005/mm6_demon_native_animations.blend',
                                         stage.parent/'animations_native_v2_20261005/mm6_demon_native_animations.glb']})
(stage/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print('All delivered-package checks passed.', flush=True)
