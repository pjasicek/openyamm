"""Leg damping for a floor-length dress (m312): the source death strides back wide and kicks the legs up, which a dress
cannot cover (the shoes left the hem by 40 cm). Per frame every leg bone (thigh, calf, foot, toe; local rotation) is
slerped from Standing's frame-0 pose toward the source by KEEP (default 0.3), so the legs stay together under the
skirt and lie straight in the corpse; pelvis and upper body keep the source motion (the floor pass in
caster_timing.py then keeps the body above the floor). Args: -- <in> <out> <Action>[:keep] [...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
LEGS = [b.name for b in rig.data.bones if b.name.startswith('B_') and any(t in b.name for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


use(bpy.data.actions['Standing']); scene.frame_set(0)
ST = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in LEGS}
for it in items:
    name, keep = (it.split(':') + [os.environ.get('KEEP', '0.3')])[:2]; keep = float(keep)
    act = bpy.data.actions[name]; use(act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    keys = {}
    for f in range(f0, f1 + 1):
        scene.frame_set(f); keys[f] = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in LEGS}
    for f, qs in keys.items():
        for n, q in qs.items():
            s = ST[n] if ST[n].dot(q) >= 0 else -ST[n]
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = s.slerp(q, keep)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'LEGDAMP {name}: legs keep {keep:.2f} of the source motion over {f1 - f0 + 1} frames')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
