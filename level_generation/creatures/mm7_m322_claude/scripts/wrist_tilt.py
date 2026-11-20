"""Hammer-hold wrist cock (m302): the source grip (Armed idle, hammer grip) carries the club level out of the thumb side,
the native peasant (m302sa0..4, walk) lets it angle down and forward toward the knee. Per clip a constant ulnar
deviation of the right hand: a rotation in B_R_Hand's local frame turning the grip axis (work/grip_pose.json) toward
the hand's distal axis (+Y) by DEG, optionally faded out from frame A to frame B (the death lays the club down).
Runs after clip_timing.py, before the club clearance and the twist rebake. Args: -- <in> <out> <Action>:<deg>[:<A>-<B>] ..."""
import bpy, sys, os, json, math
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
ax = Vector(G['handle_axis_hand_local']).normalized()
axis = ax.cross(Vector((0, 1, 0))).normalized()
print('CARRY wrist tilt axis (hand local)', [round(x, 3) for x in axis], 'grip axis vs hand Y deg',
      round(math.degrees(ax.angle(Vector((0, 1, 0)))), 1))
for it in items:
    p = it.split(':'); act = bpy.data.actions[p[0]]; deg = float(p[1])
    fa, fb = (int(x) for x in p[2].split('-')) if len(p) > 2 else (None, None)
    fc = next(c for c in act.fcurves if c.data_path == 'pose.bones["B_R_Hand"].rotation_quaternion' and c.array_index == 0) \
        if hasattr(act, 'fcurves') else None
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    pb = rig.pose.bones['B_R_Hand']; qs = []
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f); qs.append(pb.rotation_quaternion.copy())
    for f, q in zip(range(f0, f1 + 1), qs):
        w = 1.0
        if fa is not None:
            w = 1.0 if f <= fa else 0.0 if f >= fb else 0.5 + 0.5 * math.cos(math.pi * (f - fa) / (fb - fa))
        pb.rotation_quaternion = q @ Quaternion(axis, math.radians(deg) * w)
        pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'CARRY {p[0]}: wrist cocked {deg:.0f} deg' + (f', faded out over frames {fa}-{fb}' if fa is not None else ''))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
