"""Clip-layer contact fix: a smooth, temporary abduction of one upper arm about the chest's forward axis over a frame
window (the forearm and hand follow). Used where G6 finds a hand in the body because our proportions differ from the
source's (Death: the right hand sinks 5 cm into the raised right knee at the kneel; the source thigh is longer).
Args: -- <in blend> <out blend> <action> <side L|R> <deg out> <f_in> <f_full0> <f_full1> <f_out>
(the sign is defined for a hanging arm: a raised arm moves out with a NEGATIVE angle)
(0 before f_in, ramps to full by f_full0, full until f_full1, back to 0 at f_out; smoothstep ramps)."""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, action, side, deg = a[0], a[1], a[2], a[3], float(a[4])
f_in, f0, f1, f_out = (float(x) for x in a[5:9])
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
sign = 1.0 if side == 'L' else -1.0                      # +angle about forward turns a hanging arm toward +X (out for L)
bn = f'B_{side}_UpperArm'


def w(f):
    if f <= f_in or f >= f_out:
        return 0.0
    t = (f - f_in) / (f0 - f_in) if f < f0 else ((f_out - f) / (f_out - f1) if f > f1 else 1.0)
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


fr0, fr1 = (int(x) for x in act.frame_range)
mats = {}
for f in range(fr0, fr1 + 1):
    if w(f) <= 0:
        continue
    scene.frame_set(f)
    ch = rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix
    fwd = (ch.to_3x3() @ CHEST_FWD).normalized()
    pb = rig.pose.bones[bn]
    M = rig.matrix_world @ pb.matrix
    R = Matrix.Rotation(sign * math.radians(deg) * w(f), 3, fwd) @ M.to_3x3().normalized()
    M2 = R.to_4x4(); M2.translation = M.translation
    mats[f] = rig.matrix_world.inverted() @ M2
for f, M in mats.items():
    scene.frame_set(f)
    pb = rig.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'
    pb.matrix = M
    bpy.context.view_layer.update()
    pb.keyframe_insert('rotation_quaternion', frame=f)
print('ARMOFFSET', action, side, deg, 'frames changed', len(mats))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
