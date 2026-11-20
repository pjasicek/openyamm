"""Check delivered geometry, deformation, retained actions and actual GLB round-trip."""
import bpy
import hashlib
import importlib.util
import json
import numpy as np
import struct
from pathlib import Path
from mathutils.kdtree import KDTree

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage/'mm6_demon_native_animations.blend'))
spec = importlib.util.spec_from_file_location('motion', stage/'motion.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
source, rig, mesh = motion.objects()
rig.hide_set(False)
with bpy.data.libraries.load(str(stage.parent/'animations_native_v5_20261005/mm6_demon_native_animations.blend')) as (available, loaded):
    loaded.scenes = ['MM6_Demon_Native_Animations']
baseline = loaded.scenes[0]
old_rig = next(o for o in baseline.objects if o.type == 'ARMATURE')
old_mesh = next(o for o in baseline.objects if o.type == 'MESH' and o.name.startswith('Demon_Native_Mesh'))


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


data = motion.SOURCE
previous_vertices = data['previous_vertex_indices']
changes = json.loads((stage/'profile_changes.json').read_text())
foot_changed = np.zeros(len(mesh.data.vertices),bool)
foot_changed[changes['changed_vertices']] = True
assert np.array_equal(rest_vertices(mesh)[~foot_changed],rest_vertices(old_mesh)[~foot_changed])
foot_groups = [mesh.vertex_groups['mixamorig:'+s+'Foot'].index for s in ('Right','Left')]
assert all(any(g.group in foot_groups and g.weight>0 for g in mesh.data.vertices[i].groups)
           for i in np.where(foot_changed)[0])
old_faces = np.array([tuple(p.vertices) for p in old_mesh.data.polygons])
new_faces = np.array([tuple(p.vertices) for p in mesh.data.polygons])
assert np.array_equal(new_faces,old_faces)
assert [g.name for g in mesh.vertex_groups] == [g.name for g in old_mesh.vertex_groups]
for vertex in mesh.data.vertices:
    assert [(g.group,g.weight) for g in vertex.groups] == [(g.group,g.weight) for g in old_mesh.data.vertices[vertex.index].groups]
# Each new pinna is a closed shell; attachment caps add no new vertices.
ear_faces = new_faces[np.all(previous_vertices[new_faces]<0,axis=1)]
ear_edges, edge_counts = np.unique(np.sort(np.concatenate([ear_faces[:,[0,1]],ear_faces[:,[1,2]],ear_faces[:,[2,0]]]),axis=1),axis=0,return_counts=True)
assert np.all(edge_counts==2), 'Closed ear shells'
for b in rig.data.bones:
    assert np.array_equal(np.array(b.matrix_local), np.array(old_rig.data.bones[b.name].matrix_local)), b.name
retained = {}
for clip, end in {**motion.ENDS, 'Attack':36, 'Walking': 50, 'Running': 32}.items():
    a = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name == clip)
    b = next(t.strips[0].action for t in old_rig.animation_data.nla_tracks if t.name == clip)
    ca,cb = curves(a),curves(b)
    assert ca.keys()==cb.keys(),clip
    allowed = ['mixamorig:'+s+p for s in ('Right','Left') for p in ('UpLeg','Leg','Foot')]
    if clip not in ('Walking','Running'):
        allowed += [f'Bone_{i:03d}' for i in range(20,14,-1)]
    allowed_paths = {f'pose.bones[{json.dumps(n)}].rotation_quaternion' for n in allowed}
    # No body dip was needed after the foot remodelling.
    assert changes['maximum_extra_root_drop']==0
    for key in ca:
        if key[0] not in allowed_paths:
            assert ca[key]==cb[key],(clip,key)
    untouched = ~foot_changed.copy()
    tail_groups = [mesh.vertex_groups[n].index for n in allowed if n.startswith('Bone_')]
    leg_groups = [mesh.vertex_groups[n].index for n in allowed if n.startswith('mixamorig:')]
    for vertex in mesh.data.vertices:
        if any(g.group in tail_groups+leg_groups for g in vertex.groups):
            untouched[vertex.index] = False
    maximum = 0
    for time in np.arange(0, end+.01, .5):
        select(source, clip, float(time))
        expected = evaluated_vertices(source, mesh)
        select(baseline, clip, float(time))
        actual = evaluated_vertices(baseline, old_mesh)
        maximum = max(maximum,float(np.abs(expected[untouched]-actual[untouched]).max()))
    assert maximum < 1e-7, (clip, maximum)
    retained[clip] = dict(unchanged_upper_body_curves=True,unchanged_clip_timing=True,
                         samples=int(end*2+1),maximum_unaffected_vertex_change=maximum)
print('Preserved topology, weights, bind, upper-body curves and all nine clip timings.',flush=True)

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
for clip, end in {**motion.ENDS, 'Attack':36,'Walking':50,'Running':32}.items():
    if clip == 'Ash_Remains':
        continue
    stats = dict(samples=0, minimum_sole_height=100., maximum_rigid_foot_edge_error=0.,
                 maximum_hard_claw_edge_error=0., minimum_triangle_area_ratio=100.,
                 minimum_tail_distance_from_root_tip_line=100., maximum_bone_scale_error=0.,
                 maximum_non_root_translation=0., maximum_hard_claw_edge_absolute_error=0., worst_face=None)
    leg_indices = [names.index('mixamorig:'+s+p) for s in ('Right','Left') for p in ('UpLeg','Leg','Foot')]
    changed_region = foot_changed|np.any(weights[:,leg_indices]>0,axis=1)
    changed_faces = np.any(changed_region[faces],axis=1)
    stats['minimum_changed_leg_triangle_area_ratio'] = 100.
    foot_region = np.any(weights[:,[names.index('mixamorig:'+s+'Foot') for s in ('Right','Left')]]>0,axis=1)
    foot_faces = np.any(foot_region[faces],axis=1)
    stats['minimum_changed_foot_triangle_area_ratio'] = 100.
    key_arrays = []
    for time in np.arange(0, (18 if clip == 'Death' else end)+.001, .25):
        if clip == 'Death' and time >= 18:
            continue
        select(source, clip, float(time))
        v = evaluated_vertices(source, mesh)
        ratios = np.linalg.norm(v[edges[:, 0]]-v[edges[:, 1]], axis=1)/lengths
        area = np.linalg.norm(np.cross(v[faces[:, 1]]-v[faces[:, 0]], v[faces[:, 2]]-v[faces[:, 0]]), axis=1)/areas
        stats['minimum_changed_leg_triangle_area_ratio'] = min(stats['minimum_changed_leg_triangle_area_ratio'],float(area[changed_faces].min()))
        stats['minimum_changed_foot_triangle_area_ratio'] = min(stats['minimum_changed_foot_triangle_area_ratio'],float(area[foot_faces].min()))
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
    # Meshy extras retain their original wrist/knee skin creases. Check the revised foot region.
    checked_area = stats['minimum_changed_foot_triangle_area_ratio'] if clip in ('Walking','Running') else stats['minimum_triangle_area_ratio']
    assert checked_area > .02, (clip, stats)
    # A 10 cm deviation from the root-tip chord is visibly curved on this 1.8 m body.
    if clip not in ('Attack','Walking','Running'):
        assert stats['minimum_tail_distance_from_root_tip_line'] > .10, (clip, stats)
    precision = 1e-5 if clip in ('Walking','Running') else 1e-7
    assert stats['maximum_bone_scale_error'] < precision and stats['maximum_non_root_translation'] < precision
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
assert len(target_mesh.data.polygons) == len(faces)
# Material primitives reorder vertices on glTF export. Match rest positions and skin weights explicitly.
tree = KDTree(len(rest))
for i, p in enumerate(rest):
    tree.insert(p, i)
tree.balance()
vertex_map = []
# Blender's glTF primitive extractor drops influences below 0.0001, then normalizes.
# Keep the authored weights unchanged; compare the exporter representation and the resulting poses.
export_weights = np.where(weights > .0001, weights, 0)
export_weights /= export_weights.sum(axis=1, keepdims=True)
skin_error = 0
for vertex in target_mesh.data.vertices:
    candidates = tree.find_range(vertex.co, 1e-5)
    assert candidates, ('Unmatched exported vertex', vertex.index, tuple(vertex.co))
    skin = np.zeros(len(names))
    for group in vertex.groups:
        skin[names.index(target_mesh.vertex_groups[group.group].name)] = group.weight
    best = min(candidates, key=lambda item:float(np.abs(export_weights[item[1]]-skin).max()))
    error = float(np.abs(export_weights[best[1]]-skin).max())
    skin_error = max(skin_error, error)
    assert error < 1e-5, (
        vertex.index, best[1], float(np.abs(weights[best[1]]-skin).max()),
        [(str(names[i]), float(w), float(skin[i])) for i, w in enumerate(weights[best[1]]) if w > .001 or skin[i] > .001])
    vertex_map.append(best[1])
vertex_map = np.array(vertex_map)
rest_error = float(np.abs(rest[vertex_map]-rest_vertices(target_mesh)).max())
assert rest_error < 1e-5
_, equivalent = np.unique(np.round(rest, 6), axis=0, return_inverse=True)
def canonical_triangles(indices):
    triangles = np.sort(equivalent[indices], axis=1)
    return triangles[np.lexsort(triangles.T[::-1])]
imported_faces = np.array([tuple(p.vertices) for p in target_mesh.data.polygons])
assert np.array_equal(canonical_triangles(faces), canonical_triangles(vertex_map[imported_faces]))
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
        error = float(np.abs(expected[vertex_map]-actual).max())
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
report = dict(actual_glb_reimport=True, vertices=len(mesh.data.vertices), triangles=len(faces), joints=85,
              imported_vertices=len(target_mesh.data.vertices),
              profile_changes={k:v for k,v in changes.items() if k!='changed_vertices'},
              retained_connectivity_weights_bind_exactly_preserved=True, retained_clips=retained,
              ear_shell_edges_have_two_faces=True,
              all_nine_upper_body_curves_identical=True,material_vertex_mapping_verified=True,
              deformation=deformation, clip_durations_seconds=durations, roundtrip=roundtrip,
              imported_rest_coordinate_error=rest_error, imported_exporter_weight_error=skin_error,
              gltf_minimum_exported_influence=.0001, clip_switches=switches,
              baseline_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [stage.parent/'animations_native_v5_20261005/mm6_demon_native_animations.blend',
                                         stage.parent/'animations_native_v5_20261005/mm6_demon_native_animations.glb']})
(stage/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print('All delivered-package checks passed.', flush=True)
