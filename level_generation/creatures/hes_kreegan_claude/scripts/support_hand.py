"""The left (supporting) fist on the rifle's handguard in every clip (playbook: two-handed props keep both hands on
the handle). The retargeted left hand keeps the source's hold within 3-8 cm (our arms differ); per frame:
- target: the left grip tunnel's centre on the handguard axis (rifle frame x = 0, z = HG_Z), sliding along it within
  [Y_LO, Y_HI] (the nearest point, so the arm changes least), its axis turned onto the barrel by the smallest
  rotation (the roll about the handguard stays the source's);
- weight: 1 while the source's tunnel is within NEAR of the handguard, 0 beyond FAR (the reload's cell swap, the
  fall: the source hand leaves the gun), smoothstep between, then smoothed over time (Gaussian, SIG frames);
- armik.solve (minimal change, the clip's own elbow plane) to the blended hand pose; keys B_L_UpperArm, B_L_Forearm,
  B_L_Hand. Reports the residual tunnel offset at full weight. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))
GL = json.load(open(os.path.join(HERE, 'work', 'grip_pose_L_tun.json')))
HG_Z = FR['left_centre_rifle'][2]
Y_LO, Y_HI = float(os.environ.get('Y_LO', '0.31')), float(os.environ.get('Y_HI', '0.38'))
NEAR, FAR, SIG = float(os.environ.get('NEAR', '0.09')), float(os.environ.get('FAR', '0.18')), float(os.environ.get('SIG', '1.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
cL = Vector(GL['handle_centre_hand_local']); aL = Vector(GL['handle_axis_hand_local']).normalized()
BONES = ('B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand')


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


rep = {}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); frames = list(range(f0, f1 + 1))
    tg, wt = {}, {}
    for f in frames:
        sc.frame_set(f)
        Rw = AW @ rig.pose.bones['Rifle'].matrix; Hl = AW @ rig.pose.bones['B_L_Hand'].matrix
        inv = Rw.inverted()
        c = inv @ (Hl @ cL); ax = (inv.to_3x3() @ (Hl.to_3x3() @ aL)).normalized()
        y = min(max(c.y, Y_LO), Y_HI); tc = Vector((0.0, y, HG_Z))
        d = (c - tc).length
        bar = Vector((0, 1, 0)) if ax.y >= 0 else Vector((0, -1, 0))
        if os.environ.get('BAR_SIGN'):                            # fixed tunnel direction along the barrel
            bar = Vector((0, float(os.environ['BAR_SIGN']), 0))
        q = ax.rotation_difference(bar)                           # rifle frame
        Rq = Rw.to_3x3() @ q.to_matrix() @ Rw.to_3x3().inverted()   # world
        Hrot = Rq @ Hl.to_3x3().normalized()
        Hpos = Rw @ tc - Hrot @ cL
        tg[f] = (Hpos, Hrot); wt[f] = 1.0 - smooth((d - NEAR) / (FAR - NEAR))
    # temporal smoothing of the weight (no snapping on and off)
    ws = {}
    for f in frames:
        num = den = 0.0
        for g in frames:
            k = math.exp(-0.5 * ((g - f) / SIG) ** 2) if SIG > 0 else float(g == f)
            num += k * wt[g]; den += k
        ws[f] = num / den if wt[f] > 0.999 and all(wt[g] > 0.999 for g in frames) else min(wt[f], num / den) if wt[f] < 1 else num / den
    # hkr: the fist may roll round the handguard (the tunnel stays on its axis): choose the roll that bends the wrist
    # least (armik.wrist_cost swing), ROLL_RANGE deg either way, smoothed over time (SIG frames)
    RR = float(os.environ.get('ROLL_RANGE', '0')); ER = float(os.environ.get('ELBOW_RANGE', '0'))
    # a stretched arm forces the forearm along the shoulder -> wrist line (the wrist then bends): penalise reach above
    # RMAX of the arm length by KR deg per unit (the roll moves the wrist round the tunnel centre, cL ~13 cm away)
    KR, RMAX = float(os.environ.get('KREACH', '0')), float(os.environ.get('RMAX', '0.93'))
    if RR > 0 or ER > 0:
        choice = {}
        for f in frames:
            sc.frame_set(f); base_pose = {n: rig.pose.bones[n].matrix_basis.copy() for n in BONES}
            Rw = AW @ rig.pose.bones['Rifle'].matrix; ax = (Rw.to_3x3() @ Vector((0, 1, 0))).normalized()
            S_ = (AW @ rig.pose.bones['B_L_UpperArm'].matrix).translation
            E0 = (AW @ rig.pose.bones['B_L_Forearm'].matrix).translation
            Hpos, Hrot = tg[f]; piv = Hpos + Hrot @ cL
            best = None
            for deg in range(-int(RR), int(RR) + (0 if RR >= 180 else 1), 10):
                Rq = Quaternion(ax, math.radians(deg)).to_matrix()
                hr = Rq @ Hrot; hp = piv - hr @ cL
                sw_axis = (hp - S_).normalized()
                for ph in range(-int(ER), int(ER) + 1, 15):
                    pole = S_ + Quaternion(sw_axis, math.radians(ph)) @ (E0 - S_)
                    for n in BONES: rig.pose.bones[n].matrix_basis = base_pose[n]
                    bpy.context.view_layer.update()
                    reach = armik.solve(rig, 'L', hp, pole=pole if ER > 0 else None, hand_rot=hr)
                    sw, tw_ = armik.wrist_cost(rig, 'L', hr)
                    cost = sw + 0.3 * abs(tw_) + 0.05 * abs(deg) + 0.08 * abs(ph) + KR * max(0.0, reach - RMAX)
                    if best is None or cost < best[0]: best = (cost, deg, ph)
            choice[f] = best[1:]
            for n in BONES: rig.pose.bones[n].matrix_basis = base_pose[n]
        def smooth_of(k):
            out_ = {}
            for f in frames:
                w_ = [math.exp(-0.5 * ((g - f) / 2.0) ** 2) for g in frames]
                if k == 0:                                # the roll is an angle: circular mean (range up to +-180)
                    cx = sum(ww * math.cos(math.radians(choice[g][0])) for ww, g in zip(w_, frames))
                    sy = sum(ww * math.sin(math.radians(choice[g][0])) for ww, g in zip(w_, frames))
                    out_[f] = math.degrees(math.atan2(sy, cx))
                else:
                    out_[f] = sum(ww * choice[g][k] for ww, g in zip(w_, frames)) / sum(w_)
            return out_
        sr, se = smooth_of(0), smooth_of(1)
        poles = {}
        for f in frames:
            sc.frame_set(f); Rw = AW @ rig.pose.bones['Rifle'].matrix; ax = (Rw.to_3x3() @ Vector((0, 1, 0))).normalized()
            S_ = (AW @ rig.pose.bones['B_L_UpperArm'].matrix).translation; E0 = (AW @ rig.pose.bones['B_L_Forearm'].matrix).translation
            Hpos, Hrot = tg[f]; piv = Hpos + Hrot @ cL
            hr = Quaternion(ax, math.radians(sr[f])).to_matrix() @ Hrot; hp = piv - hr @ cL
            tg[f] = (hp, hr)
            poles[f] = S_ + Quaternion((hp - S_).normalized(), math.radians(se[f])) @ (E0 - S_) if ER > 0 else None
        print('SUPPORTROLL', name, 'roll deg', round(min(sr.values()), 1), round(max(sr.values()), 1), 'elbow deg', round(min(se.values()), 1), round(max(se.values()), 1))
    else:
        poles = {f: None for f in frames}
    resid = 0.0; keys = {}
    for f in frames:
        sc.frame_set(f)
        Hl = AW @ rig.pose.bones['B_L_Hand'].matrix
        Hpos, Hrot = tg[f]; w = ws[f]
        qc = Hl.to_3x3().normalized().to_quaternion(); qt = Hrot.to_quaternion()
        if qc.dot(qt) < 0: qt = -qt
        rot = qc.slerp(qt, w).to_matrix(); pos = Hl.translation.lerp(Hpos, w)
        armik.solve(rig, 'L', pos, pole=poles[f] if w > 0.99 else None, hand_rot=rot)
        keys[f] = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in BONES}
        if w > 0.99:
            Rw = AW @ rig.pose.bones['Rifle'].matrix; Hn = AW @ rig.pose.bones['B_L_Hand'].matrix
            c = Rw.inverted() @ (Hn @ cL); resid = max(resid, math.hypot(c.x, c.z - HG_Z))
    prev = {}
    for f in frames:
        for n in BONES:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; q = keys[f][n]
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    full = sum(1 for f in frames if ws[f] > 0.99)
    rep[name] = {'frames': len(frames), 'full_weight_frames': full, 'free_frames': sum(1 for f in frames if ws[f] < 0.01),
                 'residual_mm': round(resid * 1000, 2)}
    print('SUPPORT', name, json.dumps(rep[name]))
json.dump(rep, open(os.path.join(HERE, 'work', 'support_hand.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
