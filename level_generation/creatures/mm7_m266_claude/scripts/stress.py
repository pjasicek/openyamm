"""Stress pose on a rig blend: necks bend apart and forward by different amounts, one foreleg raised, a hind leg back,
tail curled, spine bent. Keyed as action 'Stress' (frame 0) and saved to the given blend.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']


def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
order = sorted(rig.pose.bones, key=lambda b: len(b.parent_recursive))
for b in order:
    n = b.name
    if n.startswith('Neck') or n.startswith('Head'):
        k = int(n[4]) if n.startswith('Neck') else int(n[4])
        side = (k - 3) * 6.0
        rot(n, (0, 1, 0), -side)
        rot(n, (1, 0, 0), 8.0 if k % 2 else -6.0)
    elif n.startswith('Tail'):
        rot(n, (0, 0, 1), 14)
    elif n == 'Spine2':
        rot(n, (0, 0, 1), 8)
    elif n == 'UpperArm_L':
        rot(n, (1, 0, 0), -55)
    elif n == 'ForeArm_L':
        rot(n, (1, 0, 0), 60)
    elif n == 'Thigh_R':
        rot(n, (1, 0, 0), 35)
act = bpy.data.actions.new('Stress'); act.use_fake_user = True
rig.animation_data_create(); rig.animation_data.action = act
for b in rig.pose.bones:
    b.keyframe_insert('rotation_quaternion', frame=0); b.keyframe_insert('location', frame=0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
