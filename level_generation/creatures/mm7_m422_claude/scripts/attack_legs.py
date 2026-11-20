"""m422 attack lower body (user review 2026-10-20: "please use legs during his attack - he is completely inert from the
bottom down"), copied from mm7_m178_claude/scripts/attack_legs.py (same source clip). m422 changes: runs on the TIMED
clip after flatten_feet.py (frames 0..47), the rear heel peels about the BALL joint at floor level with the toes kept
flat (Toe0 counter-rotated by the peel), numbers in attack_legs.json. Original m178 notes:
(m178: The planted retarget (retarget_mixamo.py :plant) held the legs at Standing frame 0: the source
Standing Melee Attack Downward stands in a wide fencing stance and only pivots its feet (no lift), so its own leg motion
was not usable. The playbook's authored-blow rules (mm6_natm_claude author_attack.py) are layered on the planted clip:
- pelvis path: rises and draws back in the wind-up (the arm goes overhead, like m178ab..ad), then drives forward and
  sinks into a deep crouch for the swipe (m178ae..ah);
- hip yaw leads (right shoulder back in the wind-up, forward into the swipe) and the chest follows chest_lag_s later
  (B_Spine takes back the yaw change of the last 50 ms); forward lean on B_Spine;
- foot plan: the LEAD (left) foot steps forward with a sine lift and lands with the blow, then steps back to its Standing
  place in the recovery; the rear (right) heel peels about a floor-level pivot under the ball of the foot; the planted
  foot never slides (its target is fixed);
- legs by two-bone IK to the foot plan in their own knee plane; feet keep their Standing world rotation (flat soles;
  the toes stay at rest), the peeling heel turns about its pivot.
All numbers in scripts/attack_legs.json (frames of the source clip). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(HERE, 'scripts', 'attack_legs.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; FPS = 30.0
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def curve(keys, f):
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * ss((f - f0) / (f1 - f0))
    return keys[-1][1]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def leg_ik(s, T, Mf):
    th, ca, ft = f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'
    Hh = armik.W(rig, th).translation; Kk = armik.W(rig, ca).translation; Aa = armik.W(rig, ft).translation
    l1, l2 = (Kk - Hh).length, (Aa - Kk).length
    d = T - Hh; dist = min(d.length, (l1 + l2) * 0.999); u = d.normalized()
    # m422: the knee bends toward the pelvis's forward direction (the inherited knee plane let the stepping knee bow
    # 17 cm outward and through the coat side)
    fwd = (armik.W(rig, 'B_Pelvis').to_3x3().normalized() @ rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)))
    fwd.z = 0; fwd = fwd.normalized() + (Kk - Hh).normalized() * 0.0
    p = fwd - u * fwd.dot(u)
    if p.length < 1e-4:
        p = (Kk - Hh) - u * (Kk - Hh).dot(u)
    v = p.normalized()
    c = max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)))
    K = Hh + l1 * (u * c + v * math.sqrt(1 - c * c))
    q = (Kk - Hh).normalized().rotation_difference((K - Hh).normalized())
    armik.set_world(rig, th, armik.rot_world(armik.W(rig, th), q.to_matrix() @ armik.W(rig, th).to_3x3().normalized()))
    Mc = armik.W(rig, ca)
    q2 = (armik.W(rig, ft).translation - Mc.translation).normalized().rotation_difference((Hh + u * dist - Mc.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(Mc, q2.to_matrix() @ Mc.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), Mf))
    return (armik.W(rig, ft).translation - T).length


# Standing frame 0: the planted legs' feet (targets) and the ball-of-foot pivots
set_act(bpy.data.actions['Standing']); sc.frame_set(0)
FOOT0 = {s: armik.W(rig, f'B_{s}_Foot').copy() for s in 'LR'}
# heel-peel pivot: the front of the floor contact (the long toe claws reach 17 cm past the ball joint; a pivot at the
# ball pushed them 5 cm into the floor)
body = bpy.data.objects['Body']; _vg = [g.name for g in body.vertex_groups]
_ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); _m = _ev.to_mesh()
_P = np.array([tuple(body.matrix_world @ v.co) for v in _m.vertices]); _ev.to_mesh_clear()
BALL = {}
for s in 'LR':
    _fm = np.array([sum(e.weight for e in v.groups if _vg[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > 0.5 for v in body.data.vertices])
    _sole = np.where(_fm & (_P[:, 2] < _P[_fm, 2].min() + 0.02))[0]
    _k = _sole[np.argmin(_P[_sole, 1])]
    BALL[s] = Vector((float(_P[_k, 0]), float(_P[_k, 1]), float(_P[_fm, 2].min())))
    if C.get('pivot') == 'ball':                     # m422 boots: the ball joint (Toe0 head) at floor level
        tb = armik.W(rig, f'B_{s}_Toe0').translation
        BALL[s] = Vector((tb.x, tb.y, float(_P[_fm, 2].min())))
print('ATTACKLEGS heel-peel pivots', {s: [round(x, 3) for x in v] for s, v in BALL.items()})
PEL0 = armik.W(rig, 'B_Pelvis').translation.copy()
lead = C['lead']; rear = 'R' if lead == 'L' else 'L'
act = bpy.data.actions['Attack']; f0, f1 = (int(x) for x in act.frame_range)
# the planted retarget copied Standing frame 0 BEFORE foot_level/plant_feet moved its pelvis: carry that change over
set_act(act); sc.frame_set(f0); DP0 = PEL0 - armik.W(rig, 'B_Pelvis').translation
print('ATTACKLEGS pelvis carried onto the levelled Standing by', [round(x * 100, 1) for x in DP0], 'cm')
bones = [b.name for b in rig.pose.bones]
poses = []; worst_ik = 0.0; worst_at = None; lag = C['chest_lag_s'] * FPS
for f in range(f0, f1 + 1):
    set_act(act); sc.frame_set(f)
    snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    set_act(None)
    for pb in rig.pose.bones:
        pb.matrix_basis = snap[pb.name]
    bpy.context.view_layer.update()
    # pelvis: translation (back = +y, the creature faces -y) and hip yaw about world Z through the pelvis
    Mp = armik.W(rig, 'B_Pelvis')
    yaw = math.radians(curve(C['hip_yaw_deg'], f))
    Mp = Matrix.Translation(Mp.translation) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(-Mp.translation) @ Mp
    Mp.translation += DP0 + Vector((0, curve(C['pelvis_back_m'], f), curve(C['pelvis_up_m'], f)))
    armik.set_world(rig, 'B_Pelvis', Mp)
    # chest follows the hips lag later; forward lean (+ about world X tips the head toward -y)
    back = math.radians(curve(C['hip_yaw_deg'], f - lag)) - yaw
    lean = math.radians(curve(C['lean_deg'], f))
    Ms = armik.W(rig, 'B_Spine'); t = Ms.translation.copy()
    Ms = Matrix.Rotation(back, 4, 'Z') @ Matrix.Rotation(lean, 4, 'X') @ Ms; Ms.translation = t
    armik.set_world(rig, 'B_Spine', Ms)
    # foot plan
    for s in 'LR':
        M = FOOT0[s].copy(); T = M.translation.copy(); R3 = M.to_3x3()
        if s == lead:
            T += Vector((0, -curve(C['step_forward_m'], f), 0))
            for a_, b_ in C['step_windows']:
                if a_ < f < b_:
                    T.z += C['step_lift_m'] * math.sin(math.pi * (f - a_) / (b_ - a_))
        else:
            ang = math.radians(curve(C['rear_heel_peel_deg'], f))
            # heel up = rotate about the lateral axis through the ball pivot; the foot faces -y, lateral = x
            Rp = Matrix.Rotation(ang, 3, 'X')            # + about x lifts the heel (behind the pivot, +y) upward
            T = BALL[s] + Rp @ (T - BALL[s]); R3 = Rp @ R3
        miss = leg_ik(s, T, R3)
        if miss > worst_ik:
            worst_ik, worst_at = miss, (f, s)
    for s in 'LR':
        rig.pose.bones[f'B_{s}_Toe0'].matrix_basis = Matrix()
    bpy.context.view_layer.update()
    if C.get('pivot') == 'ball':                     # toes flat on the floor while the heel peels
        ang = math.radians(curve(C['rear_heel_peel_deg'], f))
        Mt = armik.W(rig, f'B_{rear}_Toe0'); tt = Mt.translation.copy()
        Mt = Matrix.Rotation(-ang, 4, 'X') @ Mt; Mt.translation = tt
        armik.set_world(rig, f'B_{rear}_Toe0', Mt)
    poses.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in bones})
set_act(act)
prev = {}
for i, f in enumerate(range(f0, f1 + 1)):
    for n in ('B_Pelvis', 'B_Spine') + tuple(f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot', 'Toe0')):
        q, l = poses[i][n]
        if n in prev and q.dot(prev[n]) < 0:
            q = -q
        prev[n] = q; pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        if n == 'B_Pelvis':
            pb.location = l; pb.keyframe_insert('location', frame=f)
set_act(None)
print(f'ATTACKLEGS lead {lead}: step {max(v for _, v in C["step_forward_m"]):.2f} m, crouch {min(v for _, v in C["pelvis_up_m"]):.2f} m, '
      f'hip yaw {min(v for _, v in C["hip_yaw_deg"]):.0f}..{max(v for _, v in C["hip_yaw_deg"]):.0f} deg, worst ankle IK miss {1000 * worst_ik:.1f} mm at {worst_at}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
