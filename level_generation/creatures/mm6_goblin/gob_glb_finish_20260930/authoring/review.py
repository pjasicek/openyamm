"""Reimport and render the delivered GLB, including risky intermediate poses."""
import bpy
import json
import math
from pathlib import Path

import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review'
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'goblin_finished.blend'))
source_scene = bpy.context.scene
source_rig = next(o for o in source_scene.objects if o.type == 'ARMATURE')
source_body = bpy.data.objects['MM6 Goblin Body']
source_actions = {k: bpy.data.actions[v] for k, v in json.loads(source_scene['actions']).items()}
scene = bpy.data.scenes.new('Delivered goblin review')
bpy.context.window.scene = scene
scene.render.fps = 48
before = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'goblin_finished.glb'))
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
body = next(o for o in scene.objects if o.type == 'MESH' and len(o.data.vertices) > 4000)
actions = {}
for action in set(bpy.data.actions) - before:
    name = action.name.rsplit('.', 1)[0] if action.name.rsplit('.', 1)[-1].isdigit() else action.name
    actions[name] = action
for track in rig.animation_data.nla_tracks:
    track.mute = True
for o in scene.objects:
    if o.type == 'MESH' and o.find_armature() != rig:
        o.hide_render = True
for pb in rig.pose.bones:
    pb.custom_shape = None

def select(sc, rg, act, frame):
    bpy.context.window.scene = sc
    rg.animation_data.action = act
    rg.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(frame), subframe=float(frame % 1))
    bpy.context.view_layer.update()

def vertices(obj):
    dep = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(dep)
    mesh = evaluated.to_mesh()
    arr = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', arr)
    arr = arr.reshape(-1, 3)
    w = np.array(evaluated.matrix_world)
    arr = arr @ w[:3, :3].T + w[:3, 3]
    evaluated.to_mesh_clear()
    return arr

checks = []
for name, action in actions.items():
    for frame in sorted(set(round(f) for f in np.linspace(*action.frame_range, 19 if name == 'MM6_Attack' else 9))):
        select(source_scene, source_rig, source_actions[name], frame)
        original = vertices(source_body)
        joint_positions = {b.name: source_rig.matrix_world @ b.matrix.translation for b in source_rig.pose.bones}
        select(scene, rig, action, frame)
        exported = vertices(body)
        error = max((rig.matrix_world @ b.matrix.translation - joint_positions[b.name]).length
                    for b in rig.pose.bones if b.name in joint_positions)
        bounds_error = float(max(abs(original.min(0) - exported.min(0)).max(),
                                 abs(original.max(0) - exported.max(0)).max()))
        checks.append(dict(action=name, frame=float(frame), joint_position_error=error,
                           body_bounds_error=bounds_error, minimum_z=float(exported[:, 2].min())))
select(scene, rig, actions['MM6_Attack'], 0)
first = vertices(body)
select(scene, rig, actions['MM6_Attack'], 36)
last = vertices(body)
seam = float(np.linalg.norm(last - first, axis=1).max())
select(scene, rig, actions['Idle_Sword'], 0)
idle = vertices(body)
idle_error = float(np.linalg.norm(last - idle, axis=1).max())
report = dict(animations={k: {'duration': (a.frame_range[1] - a.frame_range[0]) / 48} for k, a in actions.items()},
              exported_meshes=[(o.name, len(o.data.polygons)) for o in scene.objects if o.type == 'MESH' and o.find_armature() == rig],
              max_influences=max(len(v.groups) for v in body.data.vertices), attack_loop_error=seam,
              idle_transition_error=idle_error, samples=checks)
report['grip_shape'] = {o.name: {k.name: k.value for k in o.data.shape_keys.key_blocks}
                        for o in scene.objects if o.type == 'MESH' and o.data.shape_keys}

# A valid export can faithfully reproduce bad skinning. Check the intended
# constant closed grip directly, including interpolation between baked frames.
hand_name = 'mixamorig:RightHand'
bind_inverse = rig.data.bones[hand_name].matrix_local.inverted()
hand_indices = [v.index for v in body.data.vertices
                if (bind_inverse @ v.co).y > .035
                and abs((bind_inverse @ v.co).x) < .105
                and abs((bind_inverse @ v.co).z) < .105
                and sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith(hand_name)) > .05]
assert len(hand_indices) > 250
hand_samples = []
grip_initial = None
for frame in np.arange(0, 36.5, .5):
    select(scene, rig, actions['MM6_Attack'], float(frame))
    points = vertices(body)[hand_indices]
    inverse = np.array((rig.matrix_world @ rig.pose.bones[hand_name].matrix).inverted())
    local = points @ inverse[:3, :3].T + inverse[:3, 3]
    if grip_initial is None:
        grip_initial = local
    displacement = np.linalg.norm(local-grip_initial, axis=1)
    hand_samples.append({'frame': float(frame), 'maximum_grip_shape_change_m': float(displacement.max())})
report['closed_grip_deformation'] = {
    'vertices': len(hand_indices), 'samples': len(hand_samples),
    'maximum_shape_change_m': max(row['maximum_grip_shape_change_m'] for row in hand_samples),
    'frame_samples': hand_samples,
}
assert report['closed_grip_deformation']['maximum_shape_change_m'] < .0001
(OUT / 'export_verification.json').write_text(json.dumps(report, indent=2) + '\n')
assert set(actions) == set(source_actions), set(actions)
assert max(c['body_bounds_error'] for c in checks) < .0001
assert max(c['joint_position_error'] for c in checks) < .0001
assert seam < .0001 and idle_error < .0001

# Inspect the actual export, using texture shading and fixed framing.
for o in scene.objects:
    if o.type == 'MESH':
        for mat in o.data.materials:
            if mat and mat.use_nodes:
                bs = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bs and bs.inputs['Base Color'].links:
                    mat.node_tree.nodes.active = bs.inputs['Base Color'].links[0].from_node
camera_data = bpy.data.cameras.new('Goblin review camera')
camera = bpy.data.objects.new('Goblin review camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
scene.world = bpy.data.worlds.new('Goblin review world')
scene.world.color = (.045, .045, .045)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 600
scene.render.resolution_y = 650
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.display.shading.show_shadows = False
scene.view_settings.view_transform = 'Standard'

def render(name, target, vec, scale=2.45):
    target = Vector(target)
    camera.location = target + Vector(vec)
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.ortho_scale = scale
    scene.render.filepath = str(OUT / (name + '.png'))
    bpy.ops.render.render(write_still=True)

for view, direction in [('front', (0, -5, 0)), ('quarter', (-3, -5, .25)), ('back', (0, 5, .15))]:
    for frame in range(37):
        select(scene, rig, actions['MM6_Attack'], frame)
        render(f'attack_{view}_{frame:02}', (0, 0, 1.00), direction)
for name in ['Running', 'Walking', 'Hit_Reaction_1', 'Idle_Sword']:
    action = actions[name]
    for i, frame in enumerate(range(round(action.frame_range[0]), round(action.frame_range[1]) + 1)):
        select(scene, rig, action, frame)
        render(f'{name}_{i:02}', (0, 0, .95), (-2.5, -5, .25))
select(scene, rig, actions['MM6_Attack'], 0)
hand = rig.matrix_world @ rig.pose.bones['mixamorig:RightHand'].head
render('grip_front', hand, (-1, -5, 1), .48)
render('grip_back', hand, (2, 5, 1), .48)
render('feet', (0, -.035, .10), (1, -5, 2), .65)

# Save a useful camera and the authored attack selection into the editable file.
bpy.context.window.scene = source_scene
cam = camera.copy()
cam.data = camera.data.copy()
source_scene.collection.objects.link(cam)
source_scene.camera = cam
target = Vector((0, 0, 1))
cam.location = target + Vector((-3, -5, .25))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 2.45
source_rig.animation_data.action = source_actions['MM6_Attack']
source_rig.animation_data.action_slot = source_actions['MM6_Attack'].slots[0]
source_scene.frame_set(6)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.shading.color_type = 'TEXTURE'
            area.spaces.active.region_3d.view_location = target
            area.spaces.active.region_3d.view_distance = 3
            area.spaces.active.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.scenes.remove(scene)
if 'START_HERE' in bpy.data.texts:
    bpy.data.texts['START_HERE'].use_fake_user = True
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'goblin_finished.blend'))
print('REVIEW_COMPLETE', json.dumps({'max_bounds_error': max(c['body_bounds_error'] for c in checks),
                                    'loop_error': seam, 'idle_transition_error': idle_error}))
