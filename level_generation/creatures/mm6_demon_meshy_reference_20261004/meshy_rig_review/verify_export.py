import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Quaternion, Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
working = bpy.data.scenes['MM6_Demon_Rig_Repair']
rig = working.objects['Demon_Rig_Review']
obj = working.objects['Demon_Rigged_Review']
verification = bpy.data.scenes.get('MM6_Demon_Rig_Export_Verification')
new_scene = verification is None
if new_scene:
    verification = bpy.data.scenes.new('MM6_Demon_Rig_Export_Verification')
verification.render.fps = 48
bpy.context.window.scene = verification
if new_scene:
    bpy.ops.import_scene.gltf(filepath=str(stage / 'mm6_demon_rig_corrected.glb'))
imported_rig = next(item for item in verification.objects if item.type == 'ARMATURE')
imported_obj = next(item for item in verification.objects if item.type == 'MESH'
                    and any(modifier.type == 'ARMATURE' for modifier in item.modifiers))
actions = {track.name: track.strips[0].action for track in imported_rig.animation_data.nla_tracks}
for target in (rig, imported_rig):
    target.data.pose_position = 'POSE'
    for track in target.animation_data.nla_tracks:
        track.mute = True
assert set(actions) == {'Walking', 'Running'}, list(actions)
assert len(imported_rig.data.bones) == 79
expected_rest = np.array([tuple(vertex.co) for vertex in obj.data.vertices])
actual_rest = np.array([tuple(vertex.co) for vertex in imported_obj.data.vertices])
rest_error = float(np.max(np.abs(expected_rest - actual_rest)))
assert rest_error < 1e-5, {'rest_coordinate_error': rest_error}
assert [list(face.vertices) for face in imported_obj.data.polygons] == [list(face.vertices) for face in obj.data.polygons]

def evaluate(scene, target, mesh_obj, action, frame):
    bpy.context.window.scene = scene
    target.animation_data.action = action
    target.animation_data.action_slot = action.slots[0]
    scene.frame_set(int(frame), subframe=float(frame % 1))
    evaluated = mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    coords = np.array([tuple(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices])
    evaluated.to_mesh_clear()
    return coords

report = {'rest_coordinate_maximum_error': rest_error, 'triangle_indices_match': True, 'clips': {}}
for clip, end in [('Walking', 50), ('Running', 32)]:
    maximum = 0.0
    first, last = None, None
    imported_first, imported_last = None, None
    for frame in np.arange(0, end + .25, .5):
        expected = evaluate(working, rig, obj, bpy.data.actions[clip], frame)
        actual = evaluate(verification, imported_rig, imported_obj, actions[clip], frame)
        error = float(np.max(np.abs(expected - actual)))
        assert error < 1e-5, {'clip': clip, 'frame': float(frame), 'pose_coordinate_error': error}
        maximum = max(maximum, error)
        if frame == 0:
            first, imported_first = expected, actual
        if frame == end:
            last, imported_last = expected, actual
    report['clips'][clip] = {
        'quarter_native_frame_samples': end * 2 + 1,
        'pose_coordinate_maximum_error': maximum,
        'working_loop_endpoint_maximum_distance': float(np.linalg.norm(first - last, axis=1).max()),
        'exported_loop_endpoint_maximum_distance': float(np.linalg.norm(imported_first - imported_last, axis=1).max()),
        'duration_seconds': end / 48,
    }
(stage / 'export_roundtrip_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

# Remove only this check's imported objects and its temporary scene. The actual
# corrected review scene and every scene that predated this task remain open.
bpy.context.window.scene = working
for item in list(verification.objects):
    bpy.data.objects.remove(item, do_unlink=True)
bpy.data.scenes.remove(verification)
for name in ('Demon_Rig_Baseline', 'Demon_Rigged_Baseline'):
    item = bpy.data.objects.get(name)
    if item is not None:
        bpy.data.objects.remove(item, do_unlink=True)
rig.animation_data.action = bpy.data.actions['Walking']
rig.animation_data.action_slot = bpy.data.actions['Walking'].slots[0]
working.frame_start = 0
working.frame_end = 50
working.frame_set(12)
working.render.resolution_x = 1300
working.render.resolution_y = 1300
camera = working.camera
center = Vector((0, -.03, .81))
camera.data.ortho_scale = 2.05
camera.location = center + Vector((1.2, -3, .35)) * 2
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
working.render.filepath = str(stage / 'preview.png')
bpy.ops.render.render(write_still=True)
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_distance = 2.5
        area.spaces.active.region_3d.view_location = Vector((0, -.03, .85))
        area.spaces.active.region_3d.view_rotation = Quaternion((1, 0, 0, 0))
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
rig.show_in_front = False
rig.hide_set(True)
for item in working.objects:
    item.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
# Write a standalone review project containing this scene and its dependencies.
bpy.data.libraries.write(str(stage / 'mm6_demon_rig_corrected.blend'), {working}, path_remap='RELATIVE')
print('Saved standalone corrected Blender project; preserved the desktop session')
