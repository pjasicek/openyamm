"""Tier A one-handed pistol stance (2026-10-22 review: "gun is held as 2 handed"): in the listed clips the free left
arm hangs as in Standing instead of following its source (set Pistol Attack R1 bends it forward with the fist in front,
Unarmed Get Hit F1 brings both fists together in front of the gun, Pistol Reload R1 brings the left fist to the gun).
Per frame, every left-arm bone (clavicle, upper arm, forearm, hand, fingers) takes Standing frame 0's LOCAL rotation
slerped toward the clip's own by SHARE (env SHARE_<Action>, default 0): the arm follows the trunk, keeps a share of the
clip's reaction, and the clip's ease from/to Standing frame 0 still matches. Run after abduct_arms.py (Standing's
6 deg are included) and before twist_bones.py. Args: -- <in blend> <out blend> <Action> ..."""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
LEGS = ('Thigh', 'Calf', 'Foot', 'Toe')
ARM = [b.name for b in rig.data.bones if b.name.startswith('B_L_') and not any(k in b.name for k in LEGS)
       and 'Twist' not in b.name]
rig.animation_data_create()


def use(act):
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


std = bpy.data.actions['Standing']; use(std); sc.frame_set(int(std.frame_range[0])); bpy.context.view_layer.update()
REST = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARM}
for an in acts:
    share = float(os.environ.get(f'SHARE_{an}', '0'))
    act = bpy.data.actions[an]; use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    keys = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n in ARM:
            q = rig.pose.bones[n].rotation_quaternion.copy()
            if REST[n].dot(q) < 0:
                q.negate()
            keys[(n, f)] = REST[n].slerp(q, share)
    prev = {}
    for (n, f), q in sorted(keys.items(), key=lambda kv: kv[0][1]):
        if n in prev and prev[n].dot(q) < 0:                      # sign-continuous keys
            q.negate()
        prev[n] = q
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=f)
    print('LEFTARM', an, f0, f1, 'share', share, 'bones', len(ARM))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
