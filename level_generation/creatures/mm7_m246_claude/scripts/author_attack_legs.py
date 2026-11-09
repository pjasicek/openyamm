"""Authored lower body for the m246 Attack (user review 2026-10-20: the planted chop's feet took no part in the blow).
Playbook "Weapon attacks and held props" (natm author_attack.py) rules on top of the planted Mixamo chop, whose upper
body (arms, sword, chest) is kept in WORLD orientation; only the hips, legs and a lean are authored. All numbers in
attack_legs.json (frames of the final Attack clip, 30 fps; the blow is near frame 30):
- pelvis path: sinks and draws back while the sword goes overhead, then drives forward and down into the chop (the
  lunge), back to Standing over the recovery;
- hip yaw leads: the pelvis turns by HIP_YAW_K x the source chest's own yaw 50 ms LATER (so the hips lead the chest by
  50 ms); the trunk keeps the source chest's world turn (B_Spine counter-rotates);
- forward lean at the blow (B_Spine pitch about the character's lateral axis, pivot at the spine head);
- foot plan: one lunge step of the LEFT foot (opposite the sword hand) forward with a sine lift, landing just before
  the blow; a recovery step back; the rear (right) heel peels about a floor-level pivot at the ball of the foot while
  its toes stay flat; feet otherwise flat at their Standing rotation (no sliding);
- legs by two-bone IK to the foot targets (knee bend plane over the toes); the pelvis is lowered whenever a leg cannot
  reach its target;
- the blow is re-measured (fastest tip motion while the blade points forward) -> work/clip_timing.json, IMPACT.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; names = [b.name for b in rig.data.bones]
C = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attack_legs.json')))
FPS = 30


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(f)
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def apply(pose):
    set_act(None)
    for b, (q, l) in pose.items():
        pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


WM = lambda b: rig.matrix_world @ rig.pose.bones[b].matrix


def setw(b, M):
    rig.pose.bones[b].matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()


def curve(keys, f):
    """Monotone cubic (Fritsch-Carlson) through (frame, value) keys, constant outside: no stop at intermediate keys
    on a monotone run (a smoothstep per segment paused the pelvis at every key)."""
    ks = sorted(keys); x = np.array([k[0] for k in ks], float); y = np.array([k[1] for k in ks], float)
    if f <= x[0]:
        return float(y[0])
    if f >= x[-1]:
        return float(y[-1])
    h = np.diff(x); d = np.diff(y) / h; m = np.zeros(len(x))
    for i in range(1, len(x) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = int(np.searchsorted(x, f) - 1); t = (f - x[i]) / h[i]
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return float(h00 * y[i] + h10 * h[i] * m[i] + h01 * y[i + 1] + h11 * h[i] * m[i + 1])


def yaw_of(b, M=None):
    M = (M or WM(b)).to_3x3()
    fw = M @ (rig.data.bones[b].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)))
    return math.atan2(fw.x, -fw.y)


act = bpy.data.actions['Attack']; nf = int(act.frame_range[1]) + 1
poses = [sample(act, f) for f in range(nf)]
# source chest yaw per frame (relative to frame 0), for the hip lead
chest = []
for p in poses:
    apply(p); chest.append(yaw_of('B_Spine2'))
chest = np.unwrap(np.array(chest)); chest -= chest[0]
lead = C['hip_lead_s'] * FPS
hip_yaw = [C['hip_yaw_k'] * float(np.interp(min(f + lead, nf - 1), np.arange(nf), chest)) for f in range(nf)]
# home feet (frame 0 = Standing)
apply(poses[0])
HOME = {sd: (WM(f'B_{sd}_Foot').copy(), WM(f'B_{sd}_Toe0').copy()) for sd in 'LR'}
TOE_DIR = {}
for sd in 'LR':
    d = HOME[sd][1].translation - HOME[sd][0].translation; d.z = 0; TOE_DIR[sd] = d.normalized()
step = C['step']; sd_step = step['side']; sd_rear = 'R' if sd_step == 'L' else 'L'
FWD = Vector((0, -1, 0)); LAT = Vector((1, 0, 0))


def foot_target(sd, f):
    """(ankle world position, foot world rotation, toe world rotation) for frame f."""
    A0, T0 = HOME[sd]
    if sd == sd_step:
        f0, f1, r0, r1 = step['out'][0], step['out'][1], step['back'][0], step['back'][1]
        disp = FWD * step['forward'] + LAT * step.get('lateral', 0.0)
        if f <= f0 or f >= r1:
            u, lift = 0.0, 0.0
        elif f < f1:
            t = (f - f0) / (f1 - f0); u = t * t * (3 - 2 * t); lift = step['lift'] * math.sin(math.pi * t)
        elif f <= r0:
            u, lift = 1.0, 0.0
        else:
            t = (f - r0) / (r1 - r0); u = 1 - t * t * (3 - 2 * t); lift = step['lift_back'] * math.sin(math.pi * t)
        p = A0.translation + disp * u; p.z += lift
        return p, A0.to_quaternion(), T0.to_quaternion(), None
    # rear foot: heel peel about the ball (the toe joint at its rest height), toes kept flat
    peel = math.radians(curve(C['rear_heel_peel_deg'], f))
    piv = T0.translation.copy()
    axis = (T0.translation - A0.translation); axis.z = 0; axis = axis.normalized().cross(Vector((0, 0, 1)))
    R = Matrix.Rotation(-peel, 3, axis)
    if (R @ (A0.translation - piv)).z < (A0.translation - piv).z:
        R = Matrix.Rotation(peel, 3, axis)
    p = piv + R @ (A0.translation - piv)
    return p, (R.to_4x4() @ A0.to_3x3().to_4x4()).to_quaternion(), T0.to_quaternion(), math.degrees(peel)


def aim(bone, direction):
    M = WM(bone); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    R = cur.rotation_difference(direction.normalized()).to_matrix().to_4x4()
    t = M.translation.copy(); M = R @ M; M.translation = t; setw(bone, M)


stats = {'drop': 0.0, 'peel': 0.0}
for f, pose in enumerate(poses):
    apply(pose)
    spine_w = WM('B_Spine').copy()                         # the source trunk's world orientation (kept)
    P = WM('B_Pelvis')
    dy, dz = curve(C['pelvis_back_m'], f), curve(C['pelvis_down_m'], f)
    yawp = hip_yaw[f]
    T = Matrix.Translation(P.translation) @ Matrix.Rotation(yawp, 4, 'Z') @ Matrix.Translation(-P.translation)
    Pn = Matrix.Translation(Vector((0, dy, dz))) @ T @ P
    # reach: lower the pelvis while a foot target is out of reach
    targets = {sd: foot_target(sd, f) for sd in 'LR'}
    for _ in range(3):
        setw('B_Pelvis', Pn)
        need = 0.0
        for sd in 'LR':
            H = WM(f'B_{sd}_Thigh').translation; K = WM(f'B_{sd}_Calf').translation; A = WM(f'B_{sd}_Foot').translation
            L = ((K - H).length + (A - K).length) * 0.985
            v = targets[sd][0] - H
            if v.length > L:
                # lower the hip by s: |v + s z| = L -> s^2 + 2 s v.z + |v|^2 - L^2 = 0; smallest root >= 0
                disc = v.z * v.z - (v.length_squared - L * L)
                s_ = (-v.z - math.sqrt(disc)) if disc >= 0 else -v.z
                need = max(need, max(s_, 0.0))
        if need <= 1e-4:
            break
        Pn = Matrix.Translation(Vector((0, 0, -need))) @ Pn; stats['drop'] = max(stats['drop'], need)
    setw('B_Pelvis', Pn)
    # trunk: the source chest's world orientation at the moved spine head, plus the authored lean (forward = toward -Y)
    lean = math.radians(curve(C['lean_deg'], f))
    S = WM('B_Spine'); M = spine_w.copy(); M.translation = S.translation
    M = Matrix.Translation(M.translation) @ Matrix.Rotation(lean, 4, 'X') @ Matrix.Translation(-M.translation) @ M
    setw('B_Spine', M)
    # legs by IK (bend plane over the toes), feet flat / peeled, toes flat
    for sd in 'LR':
        th, ca, ft, to = f'B_{sd}_Thigh', f'B_{sd}_Calf', f'B_{sd}_Foot', f'B_{sd}_Toe0'
        H = WM(th).translation; K = WM(ca).translation; A0 = WM(ft).translation
        a, b = (K - H).length, (A0 - K).length
        Tg, fq, tq, pdeg = targets[sd]
        d = min((Tg - H).length, (a + b) * 0.999); u = (Tg - H).normalized()
        fw = TOE_DIR[sd] - u * TOE_DIR[sd].dot(u); v = fw.normalized() if fw.length > 1e-6 else Vector((0, -1, 0))
        c = (a * a + d * d - b * b) / (2 * a * d)
        Kn = H + a * (u * c + v * math.sqrt(max(0.0, 1 - c * c)))
        aim(th, Kn - H); aim(ca, Tg - WM(ca).translation)
        M = fq.to_matrix().to_4x4(); M.translation = WM(ft).translation; setw(ft, M)
        M = tq.to_matrix().to_4x4(); M.translation = WM(to).translation; setw(to, M)
        if pdeg:
            stats['peel'] = max(stats['peel'], pdeg)
    for b in ['B_Pelvis', 'B_Spine'] + [f'B_{s}_{x}' for s in 'LR' for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]:
        pose[b] = (rig.pose.bones[b].rotation_quaternion.copy(), rig.pose.bones[b].location.copy())
# write back
set_act(act)
for f, pose in enumerate(poses):
    for b in ['B_Pelvis', 'B_Spine'] + [f'B_{s}_{x}' for s in 'LR' for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]:
        pb = rig.pose.bones[b]; q, l = pose[b]
        prev = poses[f - 1][b][0] if f else None
        if prev is not None and q.dot(prev) < 0:
            q = -q; pose[b] = (q, l)
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        if b == 'B_Pelvis':
            pb.location = l; pb.keyframe_insert('location', frame=f)
set_act(None)
# blow: fastest tip motion while the blade points forward (clip_timing.py rule)
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
set_act(act); tips, hilts = [], []
for f in range(nf):
    scene.frame_set(f)
    M = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    c = M @ Vector(G['handle_centre_hand_local']); ax = (M.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
    tips.append(np.array(c + ax * 0.8)); hilts.append(np.array(c))
set_act(None)
sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1)
fwd = np.array([-(t[1] - c[1]) for t, c in zip(tips, hilts)]) / 0.8
cut = np.where(fwd[:-1] > 0.5, sp, 0.0); k = int(np.argmax(cut)); impact = (k + 0.5) / FPS
tm = json.load(open(os.path.join(HERE, 'work', 'clip_timing.json')))
tm['attack_impact_s'] = round(impact, 3); tm['attack_legs'] = 'author_attack_legs.py'
json.dump(tm, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'))
print(f'ATTACKLEGS frames {nf}, hip yaw range {math.degrees(min(hip_yaw)):+.0f}..{math.degrees(max(hip_yaw)):+.0f} deg '
      f'(lead {C["hip_lead_s"]:.2f} s), extra pelvis drop for reach {stats["drop"] * 100:.1f} cm, rear heel peel max '
      f'{stats["peel"]:.0f} deg; blow at {impact:.3f} s (tip {sp[k] * FPS:.1f} m/s); IMPACT {impact:.3f}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
