"""hkr: keep the supporting left arm short of full stretch (the set's left arm is almost straight; on the demon's
proportions the handguard then lay 1-4 cm beyond the left hand's reach, so support_hand.py left a residual).
Per frame of the listed clips: the left hand's handguard target (as support_hand.py: the left tunnel's centre on the
handguard axis, sliding within [Y_LO, Y_HI]); if the shoulder -> wrist distance it needs exceeds REACH x the arm
length, the carbine (the right hand, which carries it) moves toward the left shoulder by the shortfall, smoothed over
time (Gaussian, SIG frames; never below the frame's own shortfall); the right arm is re-solved with armik (hand
rotation kept). support_hand.py runs afterwards. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json'))); HG_Z = FR['left_centre_rifle'][2]
GL = json.load(open(os.path.join(HERE, 'work', 'grip_pose_L.json'))); cL = Vector(GL['handle_centre_hand_local'])
Y_LO, Y_HI = float(os.environ.get('Y_LO', '0.20')), float(os.environ.get('Y_HI', '0.34'))
REACH, SIG = float(os.environ.get('REACH', '0.95')), 1.5
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
BONES = ('B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand')
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
    need = {}
    for f in fr:
        sc.frame_set(f)
        Rw = AW @ rig.pose.bones['Rifle'].matrix; Hl = AW @ rig.pose.bones['B_L_Hand'].matrix
        c = Rw.inverted() @ (Hl @ cL); tc = Vector((0.0, min(max(c.y, Y_LO), Y_HI), HG_Z))
        T = Rw @ tc - Hl.to_3x3().normalized() @ cL                 # wrist target (hand rotation kept: approximate)
        S = (AW @ rig.pose.bones['B_L_UpperArm'].matrix).translation
        E = (AW @ rig.pose.bones['B_L_Forearm'].matrix).translation
        L = (E - S).length + (Hl.translation - E).length
        d = (T - S).length - REACH * L
        need[f] = (max(0.0, d), (S - T).normalized())
    keys = {}; worst = 0.0
    for f in fr:
        k = [math.exp(-0.5 * ((g - f) / SIG) ** 2) for g in fr]
        mag = max(need[f][0], sum(kk * need[g][0] for kk, g in zip(k, fr)) / sum(k))
        sc.frame_set(f)
        if mag > 1e-5:
            H = AW @ rig.pose.bones['B_R_Hand'].matrix
            armik.solve(rig, 'R', H.translation + need[f][1] * mag, hand_rot=H.to_3x3().normalized())
        keys[f] = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in BONES}
        worst = max(worst, mag)
    prev = {}
    for f in fr:
        for n in BONES:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; q = keys[f][n]
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    print('REACHFIX', name, 'max carbine shift cm', round(worst * 100, 2), 'frames moved', sum(1 for f in fr if need[f][0] > 0))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
