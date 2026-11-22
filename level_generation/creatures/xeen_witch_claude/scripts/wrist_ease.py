"""Arm gate repair at the source: a hand bent more than LIMIT deg against its forearm (the hand's basis rotation
minus its twist about the forearm axis, armik.wrist_cost) keeps only KEEP of the excess bend; the twist is untouched.
Applied to the listed <Action>:<side> before twist_bones.py (the forearm twist is baked from the final hand).
Env LIMIT (default 50), KEEP (0.3). Args: -- <in blend> <out blend> <Action>:<L|R> ..."""
import bpy, sys, os, math
from mathutils import Quaternion, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
LIMIT, KEEP = math.radians(float(os.environ.get('LIMIT', '50'))), float(os.environ.get('KEEP', '0.3'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for it in items:
    name, side = it.split(':'); act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    pb = rig.pose.bones[f'B_{side}_Hand']; pb.rotation_mode = 'QUATERNION'
    worst = [0, 0]; keys = []
    for f in range(int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        q = pb.rotation_quaternion.copy()
        sw, tw = armik.split_swing_twist(q, Vector((0, 1, 0)))
        ang = sw.angle if sw.angle <= math.pi else 2 * math.pi - sw.angle
        if ang > LIMIT:
            new = LIMIT + (ang - LIMIT) * KEEP
            ax = sw.axis if sw.angle <= math.pi else -sw.axis
            q = Quaternion(ax, new) @ Quaternion((0, 1, 0), tw)
        worst = [max(worst[0], math.degrees(ang)), max(worst[1], math.degrees(min(ang, LIMIT + (ang - LIMIT) * KEEP) if ang > LIMIT else ang))]
        keys.append(q)
    for f, q in enumerate(keys):
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'WRISTEASE {name} {side}: swing max {worst[0]:.0f} -> {worst[1]:.0f} deg')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
