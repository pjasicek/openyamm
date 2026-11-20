"""Open hands for the druidess (G5): the source clips curl the fingers into fists and grips (Unarmed guard, the cup in
Relax Drink, the casts' claws), while she casts with open palms (native ata) and holds nothing. Every finger bone's
key in every action is moved toward our open rest pose: q' = slerp(identity, q, K) (K = FINGER_K, default 0.25), so a
little of the source's finger life stays. FINGER_K_<ACTION>[_L|_R] overrides K for one action / one hand
(mm6_dru1_anim_claude: the library punch keeps the right fist, FINGER_K_ATTACK_R; the left guard is looser for G5). Args: -- <in blend> <out blend>"""
import bpy, sys, os
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
K = float(os.environ.get('FINGER_K', '0.25'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))


def fcurves(act):
    out_ = list(getattr(act, 'fcurves', []) or [])
    if not out_ and hasattr(act, 'layers'):
        out_ = [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return out_


n = 0
for act in bpy.data.actions:
    k_act = float(os.environ.get(f'FINGER_K_{act.name.upper()}', K))
    by_bone = {}
    for fc in fcurves(act):
        if 'Finger' in fc.data_path and fc.data_path.endswith('rotation_quaternion'):
            bone = fc.data_path.split('"')[1]
            by_bone.setdefault(bone, {})[fc.array_index] = fc
    for bone, fcs in by_bone.items():
        if len(fcs) != 4:
            continue
        kps = list(zip(*(fcs[i].keyframe_points for i in range(4))))
        side = '_L' if bone.startswith('B_L_') else '_R'
        k_b = float(os.environ.get(f'FINGER_K_{act.name.upper()}{side}', k_act))
        for k4 in kps:
            q = Quaternion([k.co[1] for k in k4])
            r = Quaternion().slerp(q, k_b)
            for i, k in enumerate(k4):
                d = r[i] - k.co[1]
                k.co[1] = r[i]; k.handle_left[1] += d; k.handle_right[1] += d
            n += 1
    for fc in fcurves(act):
        fc.update()
print('FINGERS relaxed', n, 'keys, K', K)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
