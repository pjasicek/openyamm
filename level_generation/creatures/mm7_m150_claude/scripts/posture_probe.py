"""Posture vs the rest pose: per sampled frame, shoulder joints (B_*_UpperArm heads) forward (-Y) and down offsets
relative to the neck base, chest pitch (B_Spine2 Y axis from vertical, + = forward) and neck pitch. Args: -- <blend> clip[:frame] ..."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']


def m():
    H = lambda n: rig.matrix_world @ rig.pose.bones[n].head
    nb = H('B_Neck'); out = {}
    for s in 'LR':
        d = H(f'B_{s}_UpperArm') - nb
        out[s] = (round(-d.y * 100, 1), round(-d.z * 100, 1))
    ax = lambda n: (rig.matrix_world.to_3x3() @ rig.pose.bones[n].matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
    pitch = lambda v: round(math.degrees(math.atan2(-v.y, v.z)), 1)
    return out, pitch(ax('B_Spine2')), pitch(ax('B_Neck'))


rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
print('POSTURE rest shoulders fwd/down cm vs neck', *m())
for item in a[1:]:
    c, _, f = item.partition(':')
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    frames = [int(f)] if f else range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 3)
    for fr in frames:
        bpy.context.scene.frame_set(fr)
        print('POSTURE', c, fr, *m())
