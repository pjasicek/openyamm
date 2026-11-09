"""m470: the ghoul's big curled claws sank 7-8 cm into its thighs in clips whose source arms hang close (Mixamo idle,
walk, head shake; G6). Per listed action and frame, each upper arm turns OUT by <deg> about the chest's forward axis
(B_Spine2's forward, character faces -Y), the forearm and hand following - the native stands with the arms held out
from the body. An optional frame window <f0>-<f1> applies it there only, ramped in and out over 6 frames (the attack's recovery,
where the arms cross in front of the chest after the reach). Writes the actions in place.
Args: -- <in blend> <out blend> <Action>:<deg>[:<f0>-<f1>] ..."""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
for it in items:
    parts = it.split(':'); name, deg = parts[0], float(parts[1])
    win = tuple(int(x) for x in parts[2].split('-')) if len(parts) > 2 else None
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        k = 1.0
        if win:
            k = min(1.0, max(0.0, (f - win[0]) / 6), max(0.0, (win[1] - f) / 6)) if win[0] <= f <= win[1] else 0.0
            k = k * k * (3 - 2 * k)
        sc.frame_set(f)
        ch = rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix
        fwd = (ch.to_3x3() @ FWD).normalized()
        for s, sign in (('L', 1), ('R', -1)):
            pb = rig.pose.bones[f'B_{s}_UpperArm']
            M = rig.matrix_world @ pb.matrix; t = M.translation.copy()
            # +angle about forward (-Y) turns a hanging arm toward +X: out for the left arm, so the right arm uses -angle
            M = Matrix.Rotation(sign * math.radians(deg * k), 4, fwd) @ M; M.translation = t
            pb.rotation_mode = 'QUATERNION'; pb.matrix = rig.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action = None
    print(f'ABDUCT {name}: upper arms out {deg} deg over {f1 - f0 + 1} frames')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
