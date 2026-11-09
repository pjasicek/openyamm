"""Blade direction (azimuth from the facing -Y, positive to the character's left; elevation), tip position and tip
speed per 1/48 s of a clip: args <blend> <action>."""
import bpy, math, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / args[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; a = bpy.data.actions[args[1]]
rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
end = a.frame_range[1] / 30; prev = None
for t in np.r_[np.arange(0, end, 1 / 48), end]:
    f = t * 30; sc.frame_set(int(f), subframe=f % 1)
    m = rig.matrix_world @ rig.pose.bones['Socket_Sword'].matrix
    d = (m.to_3x3() @ Vector((0, 1, 0))).normalized(); tip = m @ Vector((0, 1.36, 0))
    speed = (tip - prev).length * 48 if prev is not None else 0; prev = tip
    print('BLADE t %.3f az %6.1f el %6.1f tip (%.2f %.2f %.2f) speed %.2f' % (
        t, math.degrees(math.atan2(d.x, -d.y)), math.degrees(math.asin(max(-1, min(1, d.z)))), tip.x, tip.y, tip.z, speed))
