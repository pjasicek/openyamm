"""Fit the shared Sentinel turret rig and five clips; export a neutral preview until retexture returns.

Uses the rigid turret conventions and clip timing from hes_turrets_claude/build_actor_v2.py. The Sentinel owns its
round base (no separate map decoration). Only its coupling cables blend two bones. No Meshy calls or stage writes.
"""
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/sentinel_uv.blend'))
scene = bpy.context.scene
scene.render.fps = 30; scene.render.fps_base = 1
body = bpy.data.objects['Sentinel']
pivot = Vector(body['pivot']); ring = float(body['ring_top'])
co = np.array([v.co[:] for v in body.data.vertices])
fpart = np.array([x.value for x in body.data.attributes['part'].data])
vpart = np.full(len(co), -1)
for face in body.data.polygons:
    for vi in face.vertices:
        assert vpart[vi] in (-1, fpart[face.index]), 'Moving parts share welded vertices'
        vpart[vi] = fpart[face.index]
assert set(vpart) == {0, 2, 3, 5}
bar = co[vpart == 3]
front = bar[bar[:, 1] < bar[:, 1].min() + 0.035]
sockets = {}
for name, pts in [('Upper', front[front[:, 2] > pivot.z]), ('Lower', front[front[:, 2] < pivot.z])]:
    assert len(pts) > 5
    middle = (pts.min(0) + pts.max(0)) / 2
    middle[1] = bar[:, 1].min() - 0.025
    sockets['Socket_Muzzle_' + name] = Vector(middle.tolist())
sockets['Socket_Muzzle'] = (sockets['Socket_Muzzle_Upper'] + sockets['Socket_Muzzle_Lower']) / 2


def select(objects):
    for obj in scene.objects:
        obj.select_set(obj in objects)
    bpy.context.view_layer.objects.active = objects[0]


arm = bpy.data.armatures.new('SentinelRig')
rig = bpy.data.objects.new('SentinelRig', arm); scene.collection.objects.link(rig)
select([rig]); bpy.ops.object.mode_set(mode='EDIT')
specs = [('B_Root', (0, 0, 0), (0, 0, 0.25), None),
         ('B_Head', (0, 0, ring), (0, 0, ring + 0.3), 'B_Root'),
         ('B_Barrel', pivot, pivot + Vector((0, -0.3, 0)), 'B_Head'),
         ('B_Recoil', pivot, pivot + Vector((0, -0.3, 0)), 'B_Barrel')]
for name, head, tail, parent in specs:
    bone = arm.edit_bones.new(name); bone.head = head; bone.tail = tail
    if parent:
        bone.parent = arm.edit_bones[parent]
for name, pos in sockets.items():
    bone = arm.edit_bones.new(name); bone.head = pos; bone.tail = pos + Vector((0, -0.05, 0))
    bone.parent = arm.edit_bones['B_Recoil']; bone.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
groups = {name: body.vertex_groups.new(name=name) for name, *_ in specs}
for vi, part in enumerate(vpart):
    if part == 5:
        t = float(np.clip((co[vi, 2] - 0.30) / 0.32, 0, 1))
        t = t * t * (3 - 2 * t)
        for bone, weight in [('B_Root', 1 - t), ('B_Head', t)]:
            if weight > 0:
                groups[bone].add([vi], weight, 'REPLACE')
    else:
        groups[{0: 'B_Root', 2: 'B_Head', 3: 'B_Recoil'}[int(part)]].add([vi], 1, 'REPLACE')
assert all(abs(sum(g.weight for g in v.groups) - 1) < 1e-6 for v in body.data.vertices)
body.parent = rig
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig


def rotation(name, axis, angle):
    axis = rig.data.bones[name].matrix_local.to_3x3().inverted() @ Vector(axis)
    return Quaternion(axis.normalized(), math.radians(angle))


def pose(yaw=0, roll=0, elevation=0, recoil=0):
    return {'B_Head': (rotation('B_Head', (0, 0, 1), yaw) @ rotation('B_Head', (0, 1, 0), roll), Vector()),
            'B_Barrel': (rotation('B_Barrel', (1, 0, 0), -elevation), Vector()),
            'B_Recoil': (Quaternion(), Vector((0, -recoil, 0)))}


def apply_pose(poses, update=True):
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion, bone.location = poses.get(bone.name, (Quaternion(), Vector()))
    if update:
        bpy.context.view_layer.update()


def clip(name, keys, smooth=False):
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = action
    for frame, poses in keys:
        if len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        apply_pose(poses, update=False)
        for bone in rig.pose.bones:
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            bone.keyframe_insert('location', frame=frame)
    action.use_frame_range = True; action.frame_start = keys[0][0]; action.frame_end = keys[-1][0]
    curves = [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = 'BEZIER' if smooth else 'LINEAR'
    return action


clip('Standing', [(f, pose(yaw=20 * math.sin(2 * math.pi * f / 180),
                         elevation=2 * math.sin(2 * math.pi * f / 90))) for f in range(0, 181, 5)], True)
clip('Attack', [(0, pose()), (4, pose()), (5, pose(elevation=4, recoil=0.07)),
                (9, pose(elevation=2, recoil=0.035)), (15, pose())])
clip('Hit', [(0, pose()), (2, pose(yaw=3, roll=1, elevation=2)), (4, pose(yaw=-2)),
             (6, pose(yaw=1, elevation=-1)), (12, pose())])
slump = pose(yaw=8, roll=2, elevation=-20)
clip('Death', [(0, pose()), (3, pose(elevation=3)), (24, slump),
               (30, pose(yaw=8, roll=2, elevation=-17)), (36, slump)])
clip('Dead', [(0, slump), (30, slump)])
rig.animation_data.action = bpy.data.actions['Standing']
rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
scene.frame_set(0)
select([rig, body])
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/sentinel_rig.blend'))
out = P / 'review/sentinel_rig_preview.glb'
bpy.ops.export_scene.gltf(filepath=str(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)

# Collision check on the actual deformed triangles, independent of how the components were classified.
rig.animation_data.action = None
clearance = {}
for name, poses in [('rest', pose()), ('aim_down', pose(elevation=-25)), ('aim_up', pose(elevation=25)),
                     ('attack', pose(elevation=4, recoil=0.07)), ('dead', slump)]:
    apply_pose(poses)
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = evaluated.to_mesh()
    pts = [v.co.copy() for v in mesh.vertices]
    base_faces = [list(f.vertices) for f in mesh.polygons if fpart[f.index] == 0]
    barrel_faces = [list(f.vertices) for f in mesh.polygons if fpart[f.index] == 3]
    collisions = BVHTree.FromPolygons(pts, base_faces).overlap(BVHTree.FromPolygons(pts, barrel_faces))
    clearance[name] = {'barrel_base_intersections': len(collisions), 'floor': min(v.z for v in pts)}
    evaluated.to_mesh_clear()
    assert len(collisions) == 0, (name, len(collisions))
    assert abs(clearance[name]['floor']) < 1e-5

scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.65, 0.65, 0.63); scene.display.shading.show_cavity = True
scene.render.resolution_x = scene.render.resolution_y = 850; scene.render.resolution_percentage = 100
scene.render.film_transparent = True
cam = bpy.data.objects.new('ReviewCam', bpy.data.cameras.new('ReviewCam')); scene.collection.objects.link(cam)
scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.35
for tag, poses in [('rest', pose()), ('scan', pose(yaw=20)), ('attack', pose(elevation=4, recoil=0.07)),
                   ('hit', pose(yaw=3, roll=1, elevation=2)), ('dead', slump),
                   ('aim_down', pose(elevation=-25)), ('aim_up', pose(elevation=25))]:
    apply_pose(poses)
    for view, (az, el) in {'q': (-35, 15), 'side': (90, 0)}.items():
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = Vector((0, 0.1, 0.8)) + d * 9
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(P / 'review/sentinel_geometry' / f'rig_{tag}_{view}.png')
        bpy.ops.render.render(write_still=True)
report = {'preview': str(out.relative_to(P)), 'status': 'neutral_rig_only_texture_pending',
          'triangles': sum(len(f.vertices) - 2 for f in body.data.polygons), 'pivot': list(pivot),
          'ring_top': ring, 'sockets': {name: list(v) for name, v in sockets.items()},
          'clearance': clearance, 'clips': {a.name: list(a.frame_range) for a in bpy.data.actions}}
(P / 'review/sentinel_geometry/rig.json').write_text(json.dumps(report, indent=2) + '\n')
print('RIG_READY', json.dumps(report), flush=True)
