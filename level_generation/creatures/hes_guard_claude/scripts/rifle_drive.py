"""Drive the rifle per frame, then the right hand from it (user review 2026-10-22, the 90-degree roll). The set's
clips carry an invisible rifle between the two hands; its direction is kept, its roll is not (the set's right hand does
not hold a pistol grip). Per frame of each listed clip, from the retargeted source pose:
- the rifle's target frame: origin at the right fist's tunnel centre (the source's hand position), the barrel Y such
  that the left fist's tunnel centre lies on the handguard (Y = HG_Y, Z = HG_Z: the right -> left line turned down by
  atan(HG_Z / HG_Y) in its vertical plane), Z = world up made perpendicular to the barrel (no roll: the receiver's top
  up, the grip down, the cell windows on the sides), X = Y x Z;
- the right hand's world pose = that frame x rifle_in_hand^-1 (rifle_fit.py); armik.solve (the clip's own elbow
  plane) puts the arm there;
- the barrel's pitch is kept within +-MAX_PITCH (the set's low ready pointed it 30-36 deg down and its get-hit 55 deg):
  turned about the gun's own X, so the roll stays 0;
- weight: 1 while the source hands hold one gun (|right -> left tunnel| within NEAR of HG), 0 beyond FAR (the death
  lets go), smoothed over time; at weight w < 1 the hand rotation is the slerp between the driven one and the hand
  held at its last fully driven angle to the forearm (rigid wrist: the Mixamo death's own hand flopped 128 deg); in
  RELEASE clips (Death) the weight never rises again once it has dropped.
The left fist is re-seated afterwards by support_hand.py. Reports the rifle-up angle to world up per clip.
Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))
Hr = Matrix(FR['rifle_in_hand']); HG_Y, HG_Z = FR['left_centre_rifle'][1], FR['left_centre_rifle'][2]
GR = json.load(open(os.path.join(HERE, 'work', 'grip_pose_R.json'))); GL = json.load(open(os.path.join(HERE, 'work', 'grip_pose_L.json')))
cR, cL = Vector(GR['handle_centre_hand_local']), Vector(GL['handle_centre_hand_local'])
NEAR, FAR, SIG = float(os.environ.get('NEAR', '0.08')), float(os.environ.get('FAR', '0.16')), 1.5
RELEASE = set(os.environ.get('RELEASE', 'Death').split(','))
MAX_PITCH = math.radians(float(os.environ.get('MAX_PITCH', '30')))
ALPHA = math.atan2(HG_Z, HG_Y); L0 = math.hypot(HG_Y, HG_Z)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
BONES = ('B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand')
UP = Vector((0, 0, 1))


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rifle_target(pR, pL):
    v = pL - pR; vh = v.normalized()
    w = UP - vh * UP.dot(vh)
    w = w.normalized() if w.length > 1e-6 else Vector((0, -1, 0))
    y = vh * math.cos(ALPHA) - w * math.sin(ALPHA)
    pitch = math.asin(max(-1.0, min(1.0, y.z)))
    if abs(pitch) > MAX_PITCH:
        hz = Vector((y.x, y.y, 0.0)).normalized()
        p_ = math.copysign(MAX_PITCH, pitch); y = hz * math.cos(p_) + UP * math.sin(p_)
    z = (UP - y * UP.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = pR
    return M, v.length


rep = {}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
    tg, wt = {}, {}
    for f in fr:
        sc.frame_set(f)
        HRw = AW @ rig.pose.bones['B_R_Hand'].matrix; HLw = AW @ rig.pose.bones['B_L_Hand'].matrix
        M, dist = rifle_target(HRw @ cR, HLw @ cL)
        tg[f] = M @ Hr.inverted(); wt[f] = 1.0 - smooth((abs(dist - L0) - NEAR) / (FAR - NEAR))
    ws = {}
    for f in fr:
        k = [math.exp(-0.5 * ((g - f) / SIG) ** 2) for g in fr]
        ws[f] = min(wt[f], sum(kk * wt[g] for kk, g in zip(k, fr)) / sum(k)) if wt[f] < 1 else sum(kk * wt[g] for kk, g in zip(k, fr)) / sum(k)
    if name in RELEASE:                                # once let go, the hand stays released (the lying death's hands meet again)
        held = True                                    # rigid wrist from the last held frame on (continuous there)
        for f in fr:
            held = held and ws[f] > 0.999; ws[f] = 1.0 if held else 0.0
    keys, ups = {}, []
    rel = None                                         # hand in the forearm frame at the last fully driven frame
    for f in fr:
        sc.frame_set(f)
        H = AW @ rig.pose.bones['B_R_Hand'].matrix; T = tg[f]; w = ws[f]
        Fa = (AW @ rig.pose.bones['B_R_Forearm'].matrix).to_3x3().normalized()
        if rel is not None and w < 0.999:
            qc = (Fa @ rel).to_quaternion()
        else:
            qc = H.to_3x3().normalized().to_quaternion()
        qt = T.to_3x3().normalized().to_quaternion()
        if qc.dot(qt) < 0: qt = -qt
        armik.solve(rig, 'R', H.translation.lerp(T.translation, w), hand_rot=qc.slerp(qt, w).to_matrix())
        keys[f] = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in BONES}
        if w > 0.999:
            rel = (AW @ rig.pose.bones['B_R_Forearm'].matrix).to_3x3().normalized().inverted() @ (AW @ rig.pose.bones['B_R_Hand'].matrix).to_3x3().normalized()
        Rw = AW @ rig.pose.bones['B_R_Hand'].matrix @ Hr
        if w > 0.99:
            ups.append(math.degrees((Rw.to_3x3() @ Vector((0, 0, 1))).angle(UP)))
    prev = {}
    for f in fr:
        for n in BONES:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; q = keys[f][n]
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    rep[name] = {'driven_frames': sum(1 for f in fr if ws[f] > 0.99), 'frames': len(fr),
                 'rifle_up_to_world_up_deg_max': round(max(ups), 1) if ups else None}
    print('RIFLEDRIVE', name, json.dumps(rep[name]))
json.dump(rep, open(os.path.join(HERE, 'work', 'rifle_drive.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
