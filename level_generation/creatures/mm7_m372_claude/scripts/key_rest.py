"""Key the bones starting with PREFIX at their rest pose (identity) on the first and last frame of every action
except the listed ones (m372: the bell-sleeve chains are simulated only in Death; unkeyed, they kept the simulation's
last pose in the other clips). Args: -- <in blend> <out blend> <prefix> [skip action ...]"""
import bpy, sys
from mathutils import Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, prefix, skip = a[0], a[1], a[2], set(a[3:])
bpy.ops.wm.open_mainfile(filepath=src)
rig = bpy.data.objects['Rig']; rig.animation_data_create()
bones = [pb for pb in rig.pose.bones if pb.name.startswith(prefix)]
n = 0
for act in [x for x in bpy.data.actions if x.use_fake_user and x.name not in skip]:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    for pb in bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion()
        for f in (f0, f1):
            pb.keyframe_insert('rotation_quaternion', frame=f)
    n += 1
rig.animation_data.action = None
for pb in bones:
    pb.rotation_quaternion = Quaternion()
print('KEYREST', prefix, len(bones), 'bones in', n, 'actions')
bpy.ops.wm.save_as_mainfile(filepath=out)
