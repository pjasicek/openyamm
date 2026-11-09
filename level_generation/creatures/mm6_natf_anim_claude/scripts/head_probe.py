"""Head direction over a clip: yaw and pitch (degrees) of the head's forward axis in world space (character faces -Y,
yaw 0 = straight at the target), plus chest and pelvis yaw. Usage: blender -b -P head_probe.py -- <blend> <action> [...]"""
import os, sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
fwd = {n: rig.data.bones[n].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)) for n in ('B_Head', 'B_Spine2', 'B_Pelvis')}
def yp(n):
    d = (rig.matrix_world @ rig.pose.bones[n].matrix).to_3x3() @ fwd[n]
    return math.degrees(math.atan2(d.x, -d.y)), math.degrees(math.asin(max(-1, min(1, d.z / d.length))))
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); print('CLIP', an)
    for f in range(f0, f1 + 1, max(1, (f1 - f0) // 16)):
        sc.frame_set(f); h = yp('B_Head'); c = yp('B_Spine2'); p = yp('B_Pelvis')
        print(f'  f{f:3d} head yaw {h[0]:6.1f} pitch {h[1]:6.1f} | chest yaw {c[0]:6.1f} | pelvis yaw {p[0]:6.1f}')
