"""Diagnostic: per clip and leg, the Femur's twist about its own axis relative to its parent (swing-twist split of the
local rotation), max |twist| in degrees."""
import bpy, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Crawler_Rig']; sc = bpy.context.scene
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for b in rig.pose.bones:
            if not b.name.startswith(('Femur', 'Tibia')):
                continue
            q = b.rotation_quaternion.normalized()
            tw = q.to_swing_twist('Y')[1]
            worst[b.name] = max(worst.get(b.name, 0), abs(math.degrees(tw)))
    print('TWIST', act.name, {k: round(v) for k, v in sorted(worst.items()) if v > 15})
