"""Attack: native pmn2 timing (0.75 s, 18 frames at 24 fps) with the staff held two-handed.
work/rig_v3g.blend (rig_v3 + the retargeted Mixamo 'great_sword_casting' as action GSC, scripts/retarget_fbx.py)
-> work/rig_v4.blend, action 'Attack'. Default keys (output frame -> source):
 0 idle carry pose -> 3 GSC 16 (staff drawn up behind the head, native b/c) -> 7 GSC 34 (diagonal above the brow, c)
 -> 10 GSC 45 (horizontal overhead passage, d) -> 18 idle carry pose (lowered in front back to the carry, e/f).
The clip's later frames (staff tipped down behind the head, kneeling ground plunge) are not used.
The GSC hands really share one handle (8-18 cm apart, grip axes aligned 0.86-0.97), so the clip's wrists are kept;
the left fist is solved onto the shaft at the clip's spacing; neck/head keep 20 % of the clip's rotation. The body
turn is cut to 20 % by counter-rotating the hips, hips height follows the native crouch (pelvis
-0.03/-0.05/-0.06/-0.025/-0.005 H) and drops further if a leg cannot reach, and both legs are re-solved so the feet
stay planted at the idle stance (native: no step).
Head clearance (user review: the right arm went through the head from 0.1 to 0.5 s): pass 1 finds per frame the
cheapest of: elbows out to the sides (native c/d, tried first), both grips moved back/forward, up and right (staff angle kept, both arms re-solved) plus the head ducked
forward (native c/d: chin under the shaft) / leaned left that leaves
no arm vertex inside the head/hair (staff_rig.head_penetration); the needs are widened/averaged over +-2 frames and
pass 2 applies them.
Env overrides reproduce the first attempt on Meshy's Heavy_Hammer_Swing (ATTACK_IN=rig_v3.blend ATTACK_SRC=
Heavy_Hammer_Swing ATTACK_WRIST_STRAIGHT=1 ATTACK_LEFT_SHAFT=0 ATTACK_HEAD_KEEP=1 ATTACK_KEYS=...): rejected by the
user (head tilted far sideways, deep forward fold at the strike); its retarget only fits the handle with bent wrists.
ARM_MODE 'solve' (two-hand solver with grip search) is kept for reference."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, os.environ.get('ATTACK_IN', 'rig_v3g.blend')))
import staff_rig as sr

FPS = 24
ARM_MODE = os.environ.get('ATTACK_ARM_MODE', 'fk')
KEEP_YAW = 0.2                                            # share of the clip's body turn kept (native rib yaw <= 8 deg)        # 'fk': clip arms, straight wrist; 'solve': two-hand solver
SRC = os.environ.get('ATTACK_SRC', 'GSC')
WRIST_STRAIGHT = os.environ.get('ATTACK_WRIST_STRAIGHT', '0') == '1'   # hammer: retarget only fits with bent wrists
LEFT_SHAFT = os.environ.get('ATTACK_LEFT_SHAFT', '1') == '1'           # put the left fist on the shaft
HEAD_KEEP = float(os.environ.get('ATTACK_HEAD_KEEP', '0.2'))           # share of the clip's neck/head rotation kept
# Clip timing (2026-10-10, engine action events): the native-length keys [0, 3, 7, 10, 18] squeezed the draw-up and
# the strike up to 3.3x; the keys below play the GSC segments at a uniform ~1.3x (16->34 in 11 frames, 34->45 in 7)
# with the same lead-in (3; a 4-frame lead-in flipped the left forearm 140 deg as the fist joins the shaft) and strike
# (8) frames. The blow then lands ~1.0 s in: actors.yml `events` (Attack, Cast). smooth_attack.py keys: [0, 3, 11, 21].
KEYS = json.loads(os.environ.get('ATTACK_KEYS', '[[0, ["idle", 0]], [3, ["clip", 16]], [14, ["clip", 34]], [21, ["clip", 45]], [29, ["idle", 0]]]'))
LAST = KEYS[-1][0]
OLD_KEYS = [0, 3, 7, 10, 18]                              # frames the per-frame constants below were authored on


def warp(f):
    """Old 18-frame layout frame -> this layout's frame (piecewise linear between the keys)."""
    new = [k for k, _ in KEYS]
    if len(new) != len(OLD_KEYS):
        return f * LAST / 18
    for (a, b), (c, d) in zip(zip(OLD_KEYS, OLD_KEYS[1:]), zip(new, new[1:])):
        if a <= f <= b:
            return c + (f - a) * (d - c) / (b - a)
    return f * LAST / 18
CLIP_LAST = max(s_[1] for _, s_ in KEYS if s_[0] == 'clip')
CLIP_FIRST = min(s_[1] for _, s_ in KEYS if s_[0] == 'clip')
RIGHT, LEFT = sr.Side('Right'), sr.Side('Left')
bones = [pb.name for pb in sr.arm.pose.bones]


def sample(action, frame):
    sr.set_action(action); sr.scene.frame_set(frame)
    return {n: (sr.arm.pose.bones[n].rotation_quaternion.copy() if sr.arm.pose.bones[n].rotation_mode == 'QUATERNION'
                else sr.arm.pose.bones[n].matrix_basis.to_quaternion(), sr.arm.pose.bones[n].location.copy()) for n in bones}


def feet(action, frame):
    sr.set_action(action); sr.scene.frame_set(frame)
    return {s: (sr.AW @ sr.B(s + 'Foot').matrix).copy() for s in ('Left', 'Right')}


def chest_yaw():
    lx = (sr.AW @ sr.B('LeftArm').head) - (sr.AW @ sr.B('RightArm').head)
    return math.atan2(lx.y, lx.x)


idle = sample('Idle_9', 0); idle_feet = feet('Idle_9', 0); IDLE_YAW = chest_yaw()
IDLE_HIPS = (sr.AW @ sr.B('Hips').matrix).translation.copy()
idle_mid = (idle_feet['Left'].translation + idle_feet['Right'].translation) / 2
clip_frames = {f: sample(SRC, f) for f in range(CLIP_FIRST, CLIP_LAST + 1)}
clip_axis = {}
sr.set_action(SRC + '_src' if SRC + '_src' in bpy.data.actions else SRC)
for f in range(CLIP_FIRST, CLIP_LAST + 1):
    sr.scene.frame_set(f)
    Ar0 = (sr.AW @ sr.B('RightHand').matrix).to_3x3() @ RIGHT.axis_hand
    Al0 = (sr.AW @ sr.B('LeftHand').matrix).to_3x3() @ LEFT.axis_hand
    clip_axis[f] = (Ar0.normalized() + Al0.normalized()).normalized()
HAND_GAP = 0.30
H = 1.7
CROUCH = [(warp(k), c) for k, c in
          [(0, 0.0), (3, -0.03 * H), (6, -0.05 * H), (9, -0.06 * H), (12, -0.025 * H), (15, -0.005 * H), (18, 0.0)]]
HIPS_IDLE_Z = None
cf = feet(SRC, 27); clip_mid = (cf['Left'].translation + cf['Right'].translation) / 2
SHIFT = Vector((idle_mid.x - clip_mid.x, idle_mid.y - clip_mid.y, 0))
print('STANCE shift', [round(x, 3) for x in SHIFT])


def source_pose(k):
    """Blended local pose for output frame k, and the two-hand weight w (0 = carry/free, 1 = two-handed)."""
    for (k0, s0), (k1, s1) in zip(KEYS, KEYS[1:]):
        if k0 <= k <= k1:
            break
    s0, s1 = tuple(s0), tuple(s1)
    if s0[0] == 'clip' and s1[0] == 'clip':
        c = s0[1] + (s1[1] - s0[1]) * (k - k0) / (k1 - k0)
        a, b = clip_frames[int(math.floor(c))], clip_frames[min(int(math.floor(c)) + 1, CLIP_LAST)]
        t = c - math.floor(c); w = 1.0
        ax = (clip_axis[int(math.floor(c))] * (1 - t) + clip_axis[min(int(math.floor(c)) + 1, CLIP_LAST)] * t).normalized()
        return {n: (a[n][0].slerp(b[n][0], t), a[n][1].lerp(b[n][1], t)) for n in bones}, w, ax
    else:
        a = idle if s0[0] == 'idle' else clip_frames[s0[1]]
        b = idle if s1[0] == 'idle' else clip_frames[s1[1]]
        t = (k - k0) / (k1 - k0); t = t * t * (3 - 2 * t)
        w = t if s1[0] == 'clip' else 1 - t
        ax = clip_axis[s1[1] if s1[0] == 'clip' else s0[1]]
    return {n: (a[n][0].slerp(b[n][0], t), a[n][1].lerp(b[n][1], t)) for n in bones}, w, ax


act = bpy.data.actions.new('Attack'); act.use_fake_user = True
sr.arm.animation_data.action = act
LEG = {s: (sr.D(s + 'UpLeg').head_local - sr.D(s + 'Leg').head_local).length for s in ('Left', 'Right')}
LEG2 = {s: (sr.D(s + 'Leg').head_local - sr.D(s + 'Foot').head_local).length for s in ('Left', 'Right')}
rest = {n: sr.rest3(n) for n in ('LeftUpLeg', 'LeftLeg', 'LeftFoot', 'RightUpLeg', 'RightLeg', 'RightFoot')}


def set_world(name, R3, head, frame):
    pb = sr.B(name); pb.rotation_mode = 'QUATERNION'
    M = R3.to_4x4(); M.translation = head; pb.matrix = sr.AW.inverted() @ M
    bpy.context.view_layer.update(); pb.keyframe_insert('rotation_quaternion', frame=frame)


def plant_leg(side, frame):
    """Two-bone IK: foot back on its idle position/orientation, knee toward the clip's knee direction."""
    up, lo, ft = sr.B(side + 'UpLeg'), sr.B(side + 'Leg'), sr.B(side + 'Foot')
    H = sr.AW @ up.head; K0 = sr.AW @ lo.head; target = idle_feet[side]
    A = target.translation; l1, l2 = LEG[side], LEG2[side]
    d = A - H; dist = min(d.length, (l1 + l2) * 0.999); dn = d.normalized()
    a = (l1 * l1 + dist * dist - l2 * l2) / (2 * dist); h = math.sqrt(max(l1 * l1 - a * a, 0))
    pole = K0 - H; pole = (pole - dn * pole.dot(dn)).normalized()
    K = H + dn * a + pole * h; A2 = H + dn * dist
    Ru = (sr.AW @ up.matrix).to_3x3(); Ru = (Ru @ sr.Y).rotation_difference((K - H).normalized()).to_matrix() @ Ru
    set_world(side + 'UpLeg', Ru, H, frame)
    Rl = (sr.AW @ lo.matrix).to_3x3(); Rl = (Rl @ sr.Y).rotation_difference((A2 - K).normalized()).to_matrix() @ Rl
    set_world(side + 'Leg', Rl, K, frame)
    set_world(side + 'Foot', target.to_3x3(), A2, frame)
    return (A2 - A).length


HEAD_FIX_CANDS = sorted([(1.0, fw, up, rt, hb, hr) for fw in (0.0, -0.06, 0.06) for up in (0.0, 0.08, -0.08, -0.16)
                         for rt in (0.0, 0.08, 0.16) for hb, hr in ((0, 0), (-10, 0), (-20, 8))]
                        + [(0.0, fw, up, rt, hb, hr) for fw in (0.0, -0.06, -0.12) for up in (0.0, 0.08, 0.16, 0.24)
                           for rt in (0.0, 0.06, 0.12, 0.18, 0.24) for hb, hr in ((0, 0), (-10, 0), (-20, 0), (-20, 8), (-20, 15))],
                        key=lambda c: 5 * c[0] + abs(c[1]) * 100 + abs(c[2]) * 100 + c[3] * 120 + abs(c[4]) * 0.6 + c[5] * 0.8)
NFIX = 6
ARM_BONES = [s_ + b_ for s_ in ('Right', 'Left') for b_ in ('Arm', 'ForeArm', 'Hand')] + ['Neck', 'Head']


def head_fix(k, w, a, gap, fix):
    """Arms out of the head: move both grips forward/up/right in the body frame (staff angle kept, both arms
    re-solved) and tilt the head back / lean it left. fix=None searches the cheapest clearing candidate; returns (fix, penetration)."""
    global phi_r, phi_l
    hips_, F, R = sr.body_frame(); Zv = Vector((0, 0, 1)); lat = Zv.cross(F)
    base = {n: (sr.AW @ sr.B(n).matrix).copy() for n in ARM_BONES}
    Mr = sr.AW @ sr.B('RightHand').matrix; Gr0 = Mr.translation + Mr.to_3x3() @ RIGHT.grip_hand

    def apply(c):
        c = tuple(x * w for x in c)                       # no fix in the blend frames next to the carry pose
        for n in ARM_BONES:
            sr.B(n).matrix = sr.AW.inverted() @ base[n]
        bpy.context.view_layer.update()
        eo, fw, up, rt, hb, hr = c
        if not any(c):
            return
        for bn, share in (('Neck', 0.4), ('Head', 0.6)):
            sr.rotate_bone_world(bn, lat, -hb * share)          # hb < 0: duck forward/down (native: chin under shaft)
            sr.rotate_bone_world(bn, F, -hr * share)            # lean toward the character's left, away from the right arm
        G = Gr0 + F * fw + Zv * up + R * rt
        pole_r = (sr.AW @ sr.B('RightForeArm').head) - ((sr.AW @ sr.B('RightArm').head) + G) * 0.5
        out_r = R * 0.9 + Zv * 0.4 - F * 0.1                # native c/d: elbows out to the sides, forearms above the brow
        pole_r = (pole_r.normalized() * (1 - eo) + out_r.normalized() * eo)
        r = RIGHT.solve(G, a, pole_r, phi_r) if eo > 0.5 else RIGHT.search([(G, a, c)], pole_r, phi_r)
        for bn, R3, head in (('Arm', r['Ra'], r['S']), ('ForeArm', r['Rf'], r['E']), ('Hand', r['Rh'], r['W'])):
            sr._set_world('Right' + bn, R3, head, None)
        if LEFT_SHAFT and w > 0:
            pole_l = (sr.AW @ sr.B('LeftForeArm').head) - ((sr.AW @ sr.B('LeftArm').head) + G - a * gap) * 0.5
            out_l = -R * 0.9 + Zv * 0.4 - F * 0.1
            pole_l = (pole_l.normalized() * (1 - eo) + out_l.normalized() * eo)
            l = LEFT.solve(G - a * gap, a, pole_l, phi_l) if eo > 0.5 else LEFT.search([(G - a * gap, a, gap)], pole_l, phi_l)
            for bn, key in (('Arm', 'Ra'), ('ForeArm', 'Rf'), ('Hand', 'Rh')):
                cur = (sr.AW @ sr.B('Left' + bn).matrix).to_3x3().to_quaternion()
                sr._set_world('Left' + bn, cur.slerp(l[key].to_quaternion(), w).to_matrix(), sr.AW @ sr.B('Left' + bn).head, None)
    if fix is None:
        best = None
        for c in HEAD_FIX_CANDS:
            apply(c); pen = sr.head_penetration()
            if best is None or pen[0] < best[1][0]:
                best = (c, pen)
            if pen[0] == 0:
                break
        fix = best[0]
    apply(fix)
    for n in ARM_BONES:
        sr.B(n).keyframe_insert('rotation_quaternion', frame=k)
    return fix, sr.head_penetration()


def build(fixes):
    global phi_r, phi_l, prev_off, prev_gap
    rows = []; needs = []; phi_r = phi_l = None; prev_off = None; prev_gap = None
    for k in range(0, LAST + 1):
        pose, w, clip_a = source_pose(k)
        for n, (q, loc) in pose.items():
            if n in ('mixamorig:Neck', 'mixamorig:Head'):
                q = idle[n][0].slerp(q, HEAD_KEEP)
            pb = sr.arm.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = loc
        bpy.context.view_layer.update()
        # stance: move hips so the clip stance centre sits on the idle one (weighted by how much clip is in the pose)
        hips = sr.B('Hips'); M = sr.AW @ hips.matrix; M.translation += SHIFT * w
        crouch = next(c0 + (c1 - c0) * (k - k0) / (k1 - k0) for (k0, c0), (k1, c1) in zip(CROUCH, CROUCH[1:]) if k0 <= k <= k1)
        M.translation.z = IDLE_HIPS.z + crouch; hips.matrix = sr.AW.inverted() @ M
        bpy.context.view_layer.update()
        dyaw = (chest_yaw() - IDLE_YAW + math.pi) % (2 * math.pi) - math.pi
        M = sr.AW @ hips.matrix; piv = M.translation.copy()
        M = Matrix.Translation(piv) @ Matrix.Rotation(-(1 - KEEP_YAW) * dyaw, 4, 'Z') @ Matrix.Translation(-piv) @ M
        hips.matrix = sr.AW.inverted() @ M; bpy.context.view_layer.update()
        for _ in range(3):                                    # legs must reach the planted feet (2 cm of knee bend kept)
            over = max((sr.AW @ sr.B(sd + 'UpLeg').head - idle_feet[sd].translation).length - (LEG[sd] + LEG2[sd]) + 0.02
                       for sd in ('Left', 'Right'))
            if over <= 0:
                break
            M = sr.AW @ hips.matrix; M.translation.z -= over; hips.matrix = sr.AW.inverted() @ M
            bpy.context.view_layer.update()
        for n in bones:
            pb = sr.arm.pose.bones[n]
            pb.keyframe_insert('rotation_quaternion', frame=k); pb.keyframe_insert('location', frame=k)
        miss = max(plant_leg('Left', k), plant_leg('Right', k))
        # staff: blended right hand's grip; axis between the carry axis and the clip's handle axis
        Mr = sr.AW @ sr.B('RightHand').matrix
        Gr = Mr.translation + Mr.to_3x3() @ RIGHT.grip_hand
        Ar = (Mr.to_3x3() @ RIGHT.axis_hand).normalized()                 # current (carry) staff axis
        a = (Ar * (1 - w) + clip_a * w).normalized()
        if ARM_MODE == 'fk':
            for sd in (('Right', 'Left') if WRIST_STRAIGHT else ()):   # straight wrists in the clip part (fists)
                fa = sr.B(sd + 'ForeArm'); hb = sr.B(sd + 'Hand')
                Rn = (sr.AW @ fa.matrix).to_3x3() @ (RIGHT if sd == 'Right' else LEFT).rel['Hand']
                cur = (sr.AW @ hb.matrix).to_3x3().to_quaternion()
                set_world(sd + 'Hand', cur.slerp(Rn.to_quaternion(), w).to_matrix(), sr.AW @ hb.head, k)
            if LEFT_SHAFT and w > 0:                        # left fist onto the shaft at the clip's hand spacing
                Mr = sr.AW @ sr.B('RightHand').matrix; Ml = sr.AW @ sr.B('LeftHand').matrix
                Gr = Mr.translation + Mr.to_3x3() @ RIGHT.grip_hand; a = (Mr.to_3x3() @ RIGHT.axis_hand).normalized()
                Gl = Ml.translation + Ml.to_3x3() @ LEFT.grip_hand
                gap = max(0.10, min(0.30, (Gr - Gl).dot(a)))
                pole_l = (sr.AW @ sr.B('LeftForeArm').head) - ((sr.AW @ sr.B('LeftArm').head) + Gr - a * gap) * 0.5
                l = LEFT.search([(Gr - a * gap, a, gap)], pole_l, phi_l); phi_l = l['phi']
                for bn, key in (('Arm', 'Ra'), ('ForeArm', 'Rf'), ('Hand', 'Rh')):
                    cur = (sr.AW @ sr.B('Left' + bn).matrix).to_3x3().to_quaternion()
                    set_world('Left' + bn, cur.slerp(l[key].to_quaternion(), w).to_matrix(), sr.AW @ sr.B('Left' + bn).head, k)
            fix, pen = head_fix(k, w, a, gap if (LEFT_SHAFT and w > 0) else 0.0, None if fixes is None else fixes[k])
            needs.append(fix)
            P = sr.body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm', 'mixamorig:LeftHand', 'mixamorig:LeftForeArm'))
            sa = (sr.AW @ sr.B('StaffTip').head - sr.AW @ sr.B('Staff').head).normalized(); G = sr.AW @ sr.B('Staff').head
            q = ((sr.AW @ sr.B('RightForeArm').matrix).to_3x3().inverted() @ (sr.AW @ sr.B('RightHand').matrix).to_3x3()).to_quaternion()
            row = {'k': k, 'w': round(w, 2), 'foot_miss_mm': round(miss * 1000, 1),
                   'staff_clearance_mm': round(1000 * sr.shaft_clearance(P, G, sa, below_grip=sr.GRIP_FROM_FOOT, above_grip=sr.L - sr.GRIP_FROM_FOOT, radius=0.03), 1),
                   'staff_low_z': round(min((G - sa * sr.GRIP_FROM_FOOT).z, (G + sa * (sr.L - sr.GRIP_FROM_FOOT)).z), 3),
                   'staff_up_deg': round(math.degrees(sa.angle(Vector((0, 0, 1))))), 'staff_fwd': round(sa.dot(sr.body_frame()[1]), 2),
                   'head_fix': fix, 'head_pen': pen}
            rows.append(row); print('ATTACK', row)
            continue
        hipsP, F, R = sr.body_frame()
        Pb = sr.body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm', 'mixamorig:LeftHand', 'mixamorig:LeftForeArm'))
        pole_r = (sr.AW @ sr.B('RightForeArm').head) - ((sr.AW @ sr.B('RightArm').head) + Gr) * 0.5
        steps = [-0.12, -0.06, 0.0, 0.06, 0.12] if w > 0.5 else [-0.03, 0.0, 0.03]
        cands = [(Gr + Vector((dx, dy, dz)), a, (dx, dy, dz)) for dx in steps for dy in steps for dz in steps]

        def staff_pen(c):
            G, ax, off = c
            clr = sr.shaft_clearance(Pb, G, ax, below_grip=sr.GRIP_FROM_FOOT, above_grip=sr.L - sr.GRIP_FROM_FOOT, radius=0.03)
            pen = max(0.0, 0.02 - clr) * 4000.0                       # 4 deg per mm closer than 2 cm
            if prev_off is not None:
                pen += 150.0 * (Vector(off) - Vector(prev_off)).length  # continuity of the grip offset
            pen += 40.0 * Vector(off).length
            if (G - ax * sr.GRIP_FROM_FOOT).z < 0.01 or (G + ax * (sr.L - sr.GRIP_FROM_FOOT)).z < 0.01:
                pen += 500.0                                            # staff into the floor
            return pen
        r = RIGHT.search(cands, pole_r, phi_r, staff_pen); phi_r = r['phi']; prev_off = r['tag']; RIGHT.apply(r, k)
        Gr = r['G']
        row = {'k': k, 'w': round(w, 2), 'grip_off_cm': [round(100 * x) for x in r['tag']], 'r_swing': round(r['sw'], 1),
               'r_twist': round(r['tw'], 1), 'foot_miss_mm': round(miss * 1000, 1)}
        if w > 0:
            pole_l = (sr.AW @ sr.B('LeftForeArm').head) - ((sr.AW @ sr.B('LeftArm').head) + Gr - a * HAND_GAP) * 0.5
            lc = [(Gr - a * g, a, g) for g in (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)]
            l = LEFT.search(lc, pole_l, phi_l, (lambda c: 0.0 if prev_gap is None else 200.0 * abs(c[2] - prev_gap)))
            phi_l = l['phi']; prev_gap = l['tag']
            if w < 1:                                         # blend the free left arm into the gripping one
                for bn, key in (('Arm', 'Ra'), ('ForeArm', 'Rf'), ('Hand', 'Rh')):
                    cur = (sr.AW @ sr.B('Left' + bn).matrix).to_3x3().to_quaternion()
                    set_world('Left' + bn, cur.slerp(l[key].to_quaternion(), w).to_matrix(), sr.AW @ sr.B('Left' + bn).head, k)
            else:
                LEFT.apply(l, k)
            row.update(gap=l['tag'], l_swing=round(l['sw'], 1), l_twist=round(l['tw'], 1))
        else:
            prev_gap = None
            for bn in ('Arm', 'ForeArm', 'Hand'):
                sr.B('Left' + bn).keyframe_insert('rotation_quaternion', frame=k)
        P = sr.body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm', 'mixamorig:LeftHand', 'mixamorig:LeftForeArm'))
        sa = (sr.AW @ sr.B('StaffTip').head - sr.AW @ sr.B('Staff').head).normalized(); G = sr.AW @ sr.B('Staff').head
        row['staff_clearance_mm'] = round(1000 * sr.shaft_clearance(P, G, sa, below_grip=sr.GRIP_FROM_FOOT, above_grip=sr.L - sr.GRIP_FROM_FOOT, radius=0.03), 1)
        row['staff_low_z'] = round(min((G - sa * sr.GRIP_FROM_FOOT).z, (G + sa * (sr.L - sr.GRIP_FROM_FOOT)).z), 3)
        rows.append(row)
        print('ATTACK', row)

    return rows, needs


phi_r = phi_l = None; prev_off = None; prev_gap = None
gap = 0.0
rows, needs = build(None)                                 # pass 1: cheapest clearing fix per frame
n = len(needs); sm = []
for i in range(n):                                        # widen (max over +-2) then average (+-2), never below need
    wide = [max((needs[j][c] for j in range(max(0, i - 2), min(n, i + 3))), key=abs) for c in range(NFIX)]   # largest |fix|
    sm.append(wide)
fixes = []
for i in range(n):
    avg = [sum(sm[j][c] for j in range(max(0, i - 2), min(n, i + 3))) / len(range(max(0, i - 2), min(n, i + 3))) for c in range(NFIX)]
    fixes.append(tuple(avg[c] if abs(avg[c]) >= abs(needs[i][c]) else needs[i][c] for c in range(NFIX)))
rows, _ = build(fixes)                                    # pass 2: smoothed fixes
act.use_frame_range = True; act.frame_start, act.frame_end = 0, LAST
json.dump(rows, open(os.path.join(common.WORK, 'attack_report.json'), 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, os.environ.get('ATTACK_OUT', 'rig_v4.blend')))
