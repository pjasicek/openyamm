"""Inspect actual mesh deformation in the gripping hand's local space."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review/hand_repair'
OUT.mkdir(exist_ok=True)
LABEL = sys.argv[sys.argv.index('--label')+1] if '--label' in sys.argv else 'before'
if '--glb' in sys.argv:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.render.fps = 48
    bpy.ops.import_scene.gltf(filepath=str(ROOT / 'goblin_finished.glb'))
else:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'goblin_finished.blend'))
scene = bpy.context.scene
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
body = next(o for o in scene.objects if o.type == 'MESH' and len(o.data.vertices) > 4000)
for track in rig.animation_data.nla_tracks:
    track.mute = True
rig['use_ik'] = 0
action = bpy.data.actions['MM6_Attack']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
hand = 'mixamorig:RightHand'
bind = rig.data.bones[hand].matrix_local
rest_points = np.array([(bind.inverted() @ v.co)[:] for v in body.data.vertices])
# The distal palm and fingers should move as one unchanged armed grip.
mask = np.array([p[1] > .035 and abs(p[0]) < .105 and abs(p[2]) < .105
                 for p in rest_points])
indices = np.flatnonzero(mask)
weight_totals = Counter()
for i in indices:
    for group in body.data.vertices[int(i)].groups:
        weight_totals[body.vertex_groups[group.group].name] += group.weight
parents = {name: b.parent.name if b.parent else None for name, b in rig.data.bones.items()
           if 'RightHand' in name or name.startswith('Bone_')}
initial = None
results = []
worst = (0, 0)
worst_vertices = []
joint_audit = {}
for side in ['Right', 'Left']:
    for short, child in [('Arm', 'ForeArm'), ('ForeArm', 'Hand')]:
        name, next_name = 'mixamorig:'+side+short, 'mixamorig:'+side+child
        bone = rig.data.bones[name]
        joint = rig.data.bones[next_name].head_local-bone.head_local
        joint_audit[name] = dict(bone_length=bone.length, joint_length=joint.length,
                                tail_joint_angle_degrees=math.degrees((bone.tail_local-bone.head_local).angle(joint)),
                                maximum_local_translation=0)
for sample in range(73):
    frame = sample/2
    scene.frame_set(int(frame), subframe=frame%1)
    bpy.context.view_layer.update()
    for name in [*joint_audit, hand]:
        row = joint_audit.setdefault(name, {'maximum_local_translation':0})
        row['maximum_local_translation'] = max(row['maximum_local_translation'], rig.pose.bones[name].location.length)
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    inverse = (rig.matrix_world @ rig.pose.bones[hand].matrix).inverted() @ evaluated.matrix_world
    points = np.array([(inverse @ mesh.vertices[int(i)].co)[:] for i in indices])
    evaluated.to_mesh_clear()
    if initial is None:
        initial = points
    displacement = np.linalg.norm(points-initial, axis=1)
    row = dict(frame=frame, maximum_hand_local_displacement=float(displacement.max()),
               p95_hand_local_displacement=float(np.percentile(displacement, 95)),
               right_hand_local_rotation_degrees=math.degrees(rig.pose.bones[hand].rotation_quaternion.angle))
    results.append(row)
    if row['maximum_hand_local_displacement'] > worst[1]:
        worst = (frame, row['maximum_hand_local_displacement'])
        order = np.argsort(displacement)[-15:][::-1]
        worst_vertices = [dict(index=int(indices[k]), displacement=float(displacement[k]),
                               rest_hand_position=rest_points[indices[k]].tolist(),
                               weights={body.vertex_groups[g.group].name:g.weight
                                        for g in body.data.vertices[int(indices[k])].groups}) for k in order]
report = dict(hand_vertex_count=len(indices), weights=dict(weight_totals.most_common()), parents=parents,
              samples=results, worst_frame=worst[0], worst_vertices=worst_vertices, joints=joint_audit)
(OUT / f'{LABEL}_hand_audit.json').write_text(json.dumps(report, indent=2)+'\n')
print('HAND_WARP', json.dumps(dict(frame=worst[0], maximum=worst[1], weights=dict(weight_totals.most_common()))))

# Remove occluding torso/left-arm geometry only in this unsaved diagnostic scene.
region = body.vertex_groups.new(name='Hand inspection region')
region.add([v.index for v, p in zip(body.data.vertices, rest_points)
            if -.22 < p[1] < .32 and abs(p[0]) < .16 and abs(p[2]) < .16], 1, 'REPLACE')
modifier = body.modifiers.new('Hand inspection isolation', 'MASK')
modifier.vertex_group = region.name
for obj in scene.objects:
    if obj.type == 'MESH' and obj.find_armature() != rig:
        obj.hide_render = True

scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.display.shading.show_shadows = False
scene.view_settings.view_transform = 'Standard'
data = bpy.data.cameras.new('Hand inspection')
camera = bpy.data.objects.new('Hand inspection', data)
scene.collection.objects.link(camera)
scene.camera = camera
data.type = 'ORTHO'
data.ortho_scale = .36
for frame in range(37):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    matrix = rig.matrix_world @ rig.pose.bones[hand].matrix
    target = matrix @ Vector((-.01, .11, -.01))
    local_target = Vector((-.01, .11, -.01))
    local_position = local_target + Vector((.7, .2, -1.7))
    rotation = (local_target-local_position).to_track_quat('-Z', 'Y')
    camera.matrix_world = matrix @ Matrix.Translation(local_position) @ rotation.to_matrix().to_4x4()
    scene.render.filepath = str(OUT/f'{LABEL}_hand_{frame:02}.png')
    bpy.ops.render.render(write_still=True)
print('HAND_INSPECTION_COMPLETE')
