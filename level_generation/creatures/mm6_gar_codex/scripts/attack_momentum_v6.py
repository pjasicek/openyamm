"""Add a torso-led anticipation and delivery to the selected v5 Attack only."""
import bpy
import json
import math
import shutil
from pathlib import Path
from mathutils import Quaternion, Vector

P = Path(__file__).resolve().parents[1]
W = P / 'work/attack_v6'
W.mkdir(exist_ok=True)
master = P / 'export/mm6_gar.blend'
before = W / 'before.blend'
if not before.exists():
    shutil.copy2(master, before)
    shutil.copy2(P / 'work/export_parity.json', W / 'parity_before.json')
bpy.ops.wm.open_mainfile(filepath=str(before))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene
assert scene.render.fps == 120
action = bpy.data.actions['Attack']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]

# Smooth pulses put the body's reversal before the hand's impact and let it settle afterward.
anchors = [(0, 0, 0), (.18, -3, .008), (.43, -21, .035),
           (.60, -4, .010), (.75, 13, -.065), (.88, 11, -.055),
           (1.08, 5, -.025), (1.30, 1, -.005), (1.5, 0, 0)]
def curve(t):
    for i in range(len(anchors) - 1):
        a, b = anchors[i:i + 2]
        if t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0])
            # Zero slope at extrema, harmonic slope elsewhere avoids stops between phases.
            def slope(j, k):
                if j == 0 or j == len(anchors) - 1:
                    return 0
                l, c, r = anchors[j - 1:j + 2]
                s0, s1 = (c[k] - l[k]) / (c[0] - l[0]), (r[k] - c[k]) / (r[0] - c[0])
                return 0 if s0 * s1 <= 0 else 2 * s0 * s1 / (s0 + s1)
            return [(2*u**3-3*u**2+1)*a[k] + (u**3-2*u**2+u)*(b[0]-a[0])*slope(i,k)
                    + (-2*u**3+3*u**2)*b[k] + (u**3-u**2)*(b[0]-a[0])*slope(i+1,k)
                    for k in (1, 2)]
    return [0, 0]

distribution = {'B_Pelvis': .15, 'B_Spine': .30, 'B_Spine1': .35, 'B_Spine2': .20,
                'B_Neck': -.25, 'B_Head': -.30}
poses = []
for frame in range(181):
    scene.frame_set(frame)
    lean, shift = curve(frame / 120)
    row = {}
    for name, fraction in distribution.items():
        bone = rig.pose.bones[name]
        axis = rig.data.bones[name].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
        row[name] = bone.rotation_quaternion @ Quaternion(axis, math.radians(lean * fraction))
    pelvis = rig.pose.bones['B_Pelvis']
    m = pelvis.matrix.copy()
    m.translation += Vector((0, shift, 0))
    pelvis.matrix = m
    row['location'] = pelvis.location.copy()
    poses.append(row)

paths = {rig.pose.bones[n].path_from_id('rotation_quaternion') for n in distribution}
paths.add(rig.pose.bones['B_Pelvis'].path_from_id('location'))
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in list(bag.fcurves):
                if fc.data_path in paths:
                    bag.fcurves.remove(fc)
previous = {}
for frame, row in enumerate(poses):
    for name in distribution:
        q = row[name]
        if name in previous and previous[name].dot(q) < 0:
            q.negate()
        previous[name] = q.copy()
        rig.pose.bones[name].rotation_quaternion = q
        rig.pose.bones[name].keyframe_insert('rotation_quaternion', frame=frame)
    rig.pose.bones['B_Pelvis'].location = row['location']
    rig.pose.bones['B_Pelvis'].keyframe_insert('location', frame=frame)
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                if fc.data_path in paths:
                    for key in fc.keyframe_points:
                        key.interpolation = 'LINEAR'
scene.frame_set(0)
assert all(abs(v) < 1e-8 for v in curve(0) + curve(1.5))
scene.render.fps = 120
bpy.ops.wm.save_as_mainfile(filepath=str(master))
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.name in ['Rig', 'Gargoyle', 'Rubble'] or obj.name.startswith('Socket_'):
        obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(W / 'momentum.glb'), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
    export_frame_step=1, export_skins=True, export_all_influences=True, export_attributes=False,
    export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
    export_anim_slide_to_zero=True, export_extras=True)
(W / 'authoring.json').write_text(json.dumps({'anchors_seconds_additive_lean_degrees_shift_y_m': anchors,
    'distribution': distribution, 'duration': 1.5, 'impact': .75,
    'changed_channels': [[n, 'rotation'] for n in distribution] + [['B_Pelvis', 'translation']]}, indent=2) + '\n')
