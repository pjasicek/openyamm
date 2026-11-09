"""Attack arm continuity (user review 5: staff flipped at viewer frame 5, hands rotated at 7-9 and 15): the per-frame
solves in attack_staff.py could pick a hand roll ~180 deg away from the previous frame (round shaft, equal wrist
cost), which reads as a spin between keys. Keeps the arm poses at the key frames KEYS (24 fps; the user's viewer
frames 0/6/12/20 at 48 fps) and rebuilds the frames in between: each hand's grip point, hand rotation and elbow
direction are interpolated in chest (Spine2) space and the arms are solved onto them without a roll search, with an
anatomical twist split (Side.pose_anatomical: upper-arm roll from the elbow plane, continuous forearm twist <= 90 deg,
wrist the rest), also for the frames after the last key (their own targets); the left
fist stays on the staff line (blended in over the first three frames, where it leaves the idle pose). Body, legs and
head keep the attack_staff.py result. work/rig_v4.blend in place. Env SMOOTH_BLEND/CLIP/KEYS/LAST/SIDES/EASE reuse it,
e.g. for the death's right arm (frame 14 rolled 160 deg): SMOOTH_BLEND=rig_v6.blend SMOOTH_CLIP=Death
SMOOTH_KEYS='[0, 3, 7, 12, 15, 18, 23]' SMOOTH_LAST=23 SMOOTH_SIDES=Right SMOOTH_FLOOR=1 (staff ends kept above the floor)."""
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
BLEND = os.environ.get('SMOOTH_BLEND', 'rig_v4.blend')
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, BLEND))
import staff_rig as sr
KEYS = json.loads(os.environ.get('SMOOTH_KEYS', '[0, 3, 6, 10]'))
SIDES = {n: sr.Side(n) for n in os.environ.get('SMOOTH_SIDES', 'Right,Left').split(',')}
act, (f0, f1) = sr.set_action(os.environ.get('SMOOTH_CLIP', 'Attack'))
EASE = os.environ.get('SMOOTH_EASE', '1') == '1'          # ease into the carry pose at both clip ends
FLOOR = os.environ.get('SMOOTH_FLOOR', '0') == '1'        # keep both staff ends 1.5 cm above the floor (death)


def lift_staff(G, Rh, side):
    """Smallest rotation of the hand about the grip that brings the lower staff end to 1.5 cm above the floor."""
    a = (Rh @ side.axis_hand).normalized()
    ends = ((-a, sr.GRIP_FROM_FOOT), (a, sr.L - sr.GRIP_FROM_FOOT))
    d, length = min(ends, key=lambda e: (G + e[0] * e[1]).z)
    if (G + d * length).z >= 0.015:
        return Rh
    want_z = max(-0.999, min(0.999, (0.015 - G.z) / length))
    horiz = Vector((d.x, d.y, 0)); horiz = horiz.normalized() if horiz.length > 1e-6 else Vector((1, 0, 0))
    want = horiz * math.sqrt(1 - want_z ** 2) + Vector((0, 0, want_z))
    return d.rotation_difference(want).to_matrix() @ Rh


def chest():
    return (sr.AW @ sr.B('Spine2').matrix).normalized()


def key_state(k):
    sr.scene.frame_set(k); C = chest(); Ci = C.inverted(); st = {}
    for name, side in SIDES.items():
        M = sr.AW @ sr.B(name + 'Hand').matrix
        G = M.translation + M.to_3x3() @ side.grip_hand
        S = sr.AW @ sr.B(name + 'Arm').head; E = sr.AW @ sr.B(name + 'ForeArm').head; W = M.translation
        st[name] = dict(G=Ci @ G, R=(Ci.to_3x3() @ M.to_3x3()).to_quaternion(), P=Ci.to_3x3() @ (E - (S + W) * 0.5))
    return st


states = {k: key_state(k) for k in KEYS}
ARMB = [sd + b for sd in ('Right', 'Left') for b in ('Arm', 'ForeArm', 'Hand')]
ENDS = {}
for kk in (0, f1):                                         # the carry pose at both ends (local rotations)
    sr.scene.frame_set(kk); ENDS[kk] = {n: sr.B(n).rotation_quaternion.copy() for n in ARMB}
LAST = int(os.environ.get('SMOOTH_LAST', f1 - 1))          # frames after the last key keep their own hand targets
for k in range(KEYS[-1] + 1, LAST + 1):
    states[k] = key_state(k)
spans = list(zip(KEYS, KEYS[1:])) + [(k, k) for k in range(KEYS[-1], LAST + 1)]
rows = []; prev_tw = {'Right': None, 'Left': None}
for a_, b_ in spans:
    for k in (range(a_ + 1, b_ + 1) if b_ > a_ else [a_]):
        if k == 0:
            continue
        t = (k - a_) / (b_ - a_) if b_ > a_ else 0.0
        sr.scene.frame_set(k); C = chest()
        res = {}
        for name in [n for n in ('Right', 'Left') if n in SIDES]:
            sa, sb = states[a_][name], states[b_][name]
            G = C @ sa['G'].lerp(sb['G'], t)
            Rh = (C.to_3x3().to_quaternion() @ sa['R'].slerp(sb['R'], t)).to_matrix()
            pole = C.to_3x3() @ sa['P'].lerp(sb['P'], t)
            if name == 'Left':                            # keep the left fist on the staff line through the right grip
                ax = (res['Right']['Rh'] @ SIDES['Right'].axis_hand).normalized(); Gr = res['Right']['G']
                n_in = KEYS[1] if len(KEYS) > 1 else 3    # joins the shaft by the first clip key
                w = 1.0 if k >= n_in else (k / n_in) ** 2 * (3 - 2 * k / n_in)
                Gs = Gr + ax * (G - Gr).dot(ax)
                G = G.lerp(Gs, w)
                Ra = (Rh @ SIDES['Left'].axis_hand).normalized()
                Rh = Quaternion().slerp(Ra.rotation_difference(ax), w).to_matrix() @ Rh
            if FLOOR and name == 'Right':
                Rh = lift_staff(G, Rh, SIDES['Right'])
            r = SIDES[name].pose_anatomical(G, Rh, pole, prev_tw[name]); r['G'] = G; prev_tw[name] = r['tw0']
            SIDES[name].apply(r, k); res[name] = r
        rows.append({'k': k, **{n[0] + '_wrist': (round(r_['sw'], 1), round(r_['tw'], 1)) for n, r_ in res.items()},
                     **{n[0] + '_forearm_twist': round(r_['forearm_twist']) for n, r_ in res.items()}, 'head_pen': sr.head_penetration()})
        print('SMOOTH', rows[-1])
# ease the solved arms out of / back into the carry pose's own arm rotations over the first/last two frames
for k, end in (((1, 0), (2, 0), (f1 - 2, f1), (f1 - 1, f1)) if EASE else ()):
    u = abs(k - end) / 3.0; u = u * u * (3 - 2 * u)
    sr.scene.frame_set(k)
    for n in ARMB:
        pb = sr.B(n); q = pb.rotation_quaternion.copy()
        if q.dot(ENDS[end][n]) < 0:
            q.negate()
        pb.rotation_quaternion = ENDS[end][n].slerp(q, u); pb.keyframe_insert('rotation_quaternion', frame=k)
print('QUAT_SIGN_FIX', sr.fix_quaternion_signs(act))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, BLEND))
