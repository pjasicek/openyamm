"""Retarget Mixamo FBX animations (mixamorig:* bones, T-pose rest, cm) onto the titan's Meshy rig (A-pose rest) as
source actions, after mm6_pmn2_claude/scripts/retarget_fbx.py. Args: blend fbx:ActionName [fbx:ActionName ...]; the
blend is saved in place (run on work/rig_v1.blend after build_rig_ttn.py, before build_clips_ttn.py).
Per bone, the target's rest frame is first swung so its bone direction matches the source rest direction; the fixed
offset O = S_rest^-1 @ that aligned frame then gives T(f) = S(f) @ O, so every bone points where the source bone
points and keeps the source twist. Bone names: Meshy's spine chain runs the other way (Spine02 is the lowest), see
MAP. Hips translation is not kept (build_clips_ttn.py plants hips and legs). One key per source frame; the action
stores the source rate in its 'fps' property; the scene is put back to 24 fps."""
import bpy, sys, os
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for side in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[side + b] = side + b
tgt = bpy.data.objects['Titan_Rig']
scene = bpy.context.scene
for item in args:
    fbx, name = item.rsplit(':', 1)
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    fps = scene.render.fps                                   # the FBX import switches the scene to its own rate
    src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    src_act = next(iter(set(bpy.data.actions) - acts_before))
    src.animation_data.action = src_act
    pairs = [(t, 'mixamorig:' + s) for t, s in MAP.items() if 'mixamorig:' + s in src.data.bones]
    SW, TW = src.matrix_world, tgt.matrix_world
    Y = Vector((0, 1, 0))
    offset = {}
    for t, s in pairs:
        Rs = (SW @ src.data.bones[s].matrix_local).to_3x3().normalized()
        Rt = (TW @ tgt.data.bones[t].matrix_local).to_3x3().normalized()
        swing = (Rt @ Y).rotation_difference(Rs @ Y).to_matrix()
        offset[t] = Rs.inverted() @ (swing @ Rt)
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    act = bpy.data.actions.new(name); act.use_fake_user = True; act['fps'] = fps
    tgt.animation_data_create(); tgt.animation_data.action = act
    if getattr(act, 'slots', None) and len(act.slots):
        tgt.animation_data.action_slot = act.slots[0]
    order = [b.name for b in tgt.data.bones]                  # parents first
    pairs.sort(key=lambda p: order.index(p[0]))
    f0, f1 = (int(round(x)) for x in src_act.frame_range)
    for i, f in enumerate(range(f0, f1 + 1)):
        scene.frame_set(f)
        for t, s in pairs:
            pb = tgt.pose.bones[t]
            M = ((SW @ src.pose.bones[s].matrix).to_3x3().normalized() @ offset[t]).to_4x4()
            M.translation = TW @ pb.head
            pb.rotation_mode = 'QUATERNION'
            pb.matrix = TW.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=i)
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.actions.remove(src_act)
    tgt.animation_data.action = None
    print('RETARGET', name, 'frames 0 ..', f1 - f0, 'at', fps, 'fps,', len(pairs), 'bones')
scene.render.fps = 24
bpy.ops.wm.save_mainfile()
