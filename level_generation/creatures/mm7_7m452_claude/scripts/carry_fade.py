"""Death carry with a fade (7m452 review 2026-10-20: the billhook's shaft went 5 cm through the left thigh as the
source arm swung the fist across the body in the backward fall; no wrist turn cleared it). Mode copy: duplicates
<Action> as <Action>Src. Mode fade: after author_carry.py rewrote <Action>, the right arm (clavicle to fingers, twist
bones) takes the carried pose until frame A and fades back to <Action>Src's own arm by frame B (smoothstep), so the
billhook stays at the right hip through the fall and the arm drops with the body when it lies.
Args: -- <in> <out> copy <Action> | -- <in> <out> fade <Action> <A> <B>"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
src, out, mode, name = a[:4]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


if mode == 'copy':
    old = bpy.data.actions.get(name + 'Src')
    if old:
        bpy.data.actions.remove(old)
    c = bpy.data.actions[name].copy(); c.name = name + 'Src'; c.use_fake_user = True
    print(f'CARRY copied {name} -> {c.name}')
else:
    A, B = int(a[4]), int(a[5])
    act, srca = bpy.data.actions[name], bpy.data.actions[name + 'Src']
    bones = [b.name for b in rig.data.bones if b.name.startswith('B_R_') and not any(k in b.name for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    keys = {}
    for f in range(f0, f1 + 1):
        use(act); sc.frame_set(f); car = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in bones}
        use(srca); sc.frame_set(f); own = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in bones}
        keys[f] = (car, own)
    use(act)
    for f, (car, own) in keys.items():
        x = min(1.0, max(0.0, (f - A) / max(B - A, 1))); w = 1 - x * x * (3 - 2 * x)      # 1 = carried
        for n in bones:
            q0, q1 = own[n], car[n]
            if q0.dot(q1) < 0:
                q1 = -q1
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q0.slerp(q1, w)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    bpy.data.actions.remove(srca)
    print(f'CARRY {name}: carried arm until frame {A}, faded to the source arm by {B} ({len(bones)} bones)')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
