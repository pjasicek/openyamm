"""Retarget Mixamo FBX clips (mixamorig:* bones, T-pose rest, cm, 30 fps pack) onto Skeleton_Rig (same mixamorig names,
A-pose rest) as source actions 'src_<Name>', after mm6_pmn2_claude/scripts/retarget_fbx.py and the werewolf's
multi-clip version. Per bone the target rest frame is swung onto the source rest direction; the fixed offset
O = S_rest^-1 @ aligned target then gives T(t) = S(t) @ O (bone directions and twist follow the source). Fingers are
not retargeted (the right fist comes from the grip). Keys are resampled to 24 fps (sub-frame evaluation of the
source). Hips translation is kept, scaled by the hips-height ratio (build_clips.py removes the drift).
Args: -- <blend> fbx:Name [fbx:Name ...]   (blend saved in place)"""
import bpy, sys, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, items = args[0], args[1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene
tgt = bpy.data.objects['Skeleton_Rig']
BODY = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head']
for s in ('Left', 'Right'):
    BODY += [s + b for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase')]
order = [b.name for b in tgt.data.bones]
for item in items:
    fbx, name = item.rsplit(':', 1)
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    fps = scene.render.fps / scene.render.fps_base
    src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    src_act = next(iter(set(bpy.data.actions) - acts_before))
    src.animation_data.action = src_act
    names = sorted(['mixamorig:' + b for b in BODY if 'mixamorig:' + b in src.data.bones], key=order.index)
    SW, TW = src.matrix_world, tgt.matrix_world
    Y = Vector((0, 1, 0))
    offset = {}
    for n in names:
        Rs = (SW @ src.data.bones[n].matrix_local).to_3x3().normalized()
        Rt = (TW @ tgt.data.bones[n].matrix_local).to_3x3().normalized()
        swing = (Rt @ Y).rotation_difference(Rs @ Y).to_matrix()
        offset[n] = Rs.inverted() @ (swing @ Rt)
    act_name = 'src_' + name
    if act_name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[act_name])
    act = bpy.data.actions.new(act_name); act.use_fake_user = True
    tgt.animation_data_create(); tgt.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        tgt.animation_data.action_slot = act.slots[0]
    f0, f1 = src_act.frame_range
    dur = (f1 - f0) / fps
    n_out = int(round(dur * 24))
    sh = SW @ src.data.bones['mixamorig:Hips'].head_local
    th = TW @ tgt.data.bones['mixamorig:Hips'].head_local
    k = th.z / sh.z
    for i in range(n_out + 1):
        sf = f0 + i / 24 * fps
        scene.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))
        for n in names:
            pb = tgt.pose.bones[n]
            M = ((SW @ src.pose.bones[n].matrix).to_3x3().normalized() @ offset[n]).to_4x4()
            M.translation = th + (SW @ src.pose.bones[n].head - sh) * k if n == 'mixamorig:Hips' else TW @ pb.head
            pb.rotation_mode = 'QUATERNION'
            pb.matrix = TW.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'mixamorig:Hips':
                pb.keyframe_insert('location', frame=i)
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.actions.remove(src_act)
    tgt.animation_data.action = None
    for pb in tgt.pose.bones:
        pb.matrix_basis.identity()
    print('RETARGET', act_name, 'frames 0 ..', n_out, f'({dur:.2f} s from {fps:.0f} fps)', len(names), 'bones, hips scale', round(k, 3))
scene.render.fps = 24; scene.render.fps_base = 1
bpy.ops.wm.save_mainfile()
