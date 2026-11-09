"""Wrist swing <= LIMIT on the two-handed holds without moving the gun (both fists stay on it, the rifle checks keep).
Per listed clip and side, a global (Viterbi) choice over the clip of
- phi (deg): the elbow plane turned about the shoulder -> wrist line (the hand's world position kept), and
- for the left (support) fist while it holds the handguard (support_hand.json weight 1, Rifle bone present): rho (deg),
  a roll of the whole fist about the handguard axis through its tunnel centre, and ds, a slide along it within
  [Y_LO, Y_HI] of the rifle frame (support_hand.py's range; the carbine's foregrip spans it), so it stays on it;
  the right fist keeps its world pose (it holds the pistol grip, the gun rides on it). Held = the tunnel centre within
  5 mm of the handguard axis (rifle_frame.json); frames that let go (the death's fall) only turn the elbow.
Cost per frame = max(0, swing - TARGET) * 4 + K_SW * swing + K_PHI |phi| + K_RHO |rho|, transitions
K_CONT (|dphi| + |drho|): the clip's own arm (phi = rho = 0) is kept wherever the wrist is already within TARGET, and
nothing snaps. Keys B_<s>_UpperArm, B_<s>_Forearm, B_<s>_Hand; writes work/wrist_elbow.json.
Args: -- <in blend> <out blend> <sides LR> <Action> [...]   (env: TARGET 55, HARD 59 (x40 above), PHI_MAX 60, RHO_MAX 40)"""
import bpy, sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, sides, acts = a[0], a[1], a[2], a[3:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.environ.get
HARD = float(E('HARD', '59'))
TARGET, K_SW, K_PHI, K_RHO, K_CONT = (float(E('TARGET', '55')), float(E('K_SW', '0.05')), float(E('K_PHI', '0.15')),
                                      float(E('K_RHO', '0.15')), float(E('K_CONT', '0.4')))
PM, RM = int(E('PHI_MAX', '60')), int(E('RHO_MAX', '40'))
PHIS = list(range(-PM, PM + 1, int(E('PHI_STEP', '5'))))
RHOS = list(range(-RM, RM + 1, int(E('RHO_STEP', '10'))))
SLIDES = [float(x) for x in E('SLIDES', '-0.03,-0.015,0,0.015,0.03').split(',')]
Y_LO, Y_HI, K_SL = float(E('Y_LO', '0.28')), float(E('Y_HI', '0.37')), float(E('K_SL', '30'))
HG_Z = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))['left_centre_rifle'][2]
GL = json.load(open(os.path.join(HERE, 'work', 'grip_pose_L_tun.json')))
cL = Vector(GL['handle_centre_hand_local'])
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
HAS_GUN = 'Rifle' in rig.pose.bones
rep = {}


def pose_for(s, f_state, phi, rho, ds=0.0):
    """Solve side s to the stored frame state with elbow-plane phi, handguard roll rho (deg) and slide ds (m) along
    the handguard; returns the wrist swing."""
    H, S, Eb, C, ax = f_state
    Hrot = H.to_3x3().normalized()
    if rho or ds:
        Hrot = Matrix.Rotation(math.radians(rho), 3, ax) @ Hrot
        Hpos = C + ax * ds - Hrot @ cL
    else:
        Hpos = H.translation
    u = (Hpos - S).normalized(); p0 = (Eb - S) - u * (Eb - S).dot(u)
    pole = S + Matrix.Rotation(math.radians(phi), 3, u) @ p0
    armik.solve(rig, s, Hpos, pole=pole, hand_rot=Hrot)
    return armik.wrist_cost(rig, s, Hrot)[0]


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); frames = list(range(f0, f1 + 1))
    for s in sides:
        ua, fa, hd = f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand'
        roll = s == 'L' and HAS_GUN
        states = [(phi, rho, ds) for phi in PHIS for rho in (RHOS if roll else [0]) for ds in (SLIDES if roll else [0.0])]
        cost, before, fst, floor = [], [], {}, []
        for f in frames:
            sc.frame_set(f)
            snap = {n: rig.pose.bones[n].matrix_basis.copy() for n in (ua, fa, hd)}
            H = armik.W(rig, hd).copy()
            ax = (AW @ rig.pose.bones['Rifle'].matrix).to_3x3().normalized() @ Vector((0, 1, 0)) if HAS_GUN else Vector((0, 1, 0))
            fst[f] = (H, armik.W(rig, ua).translation.copy(), armik.W(rig, fa).translation.copy(), H @ cL, ax.normalized())
            held, cy = False, 0.0
            if roll:
                c = (AW @ rig.pose.bones['Rifle'].matrix).inverted() @ (H @ cL); held = math.hypot(c.x, c.z - HG_Z) < 0.005
                cy = c.y
            before.append(armik.wrist_cost(rig, s, H.to_3x3().normalized())[0])
            row, sws = [], []
            for phi, rho, ds in states:
                if (rho or ds) and (not held or not Y_LO - 1e-4 <= cy + ds <= Y_HI + 1e-4):
                    row.append(1e6); continue
                for n in (ua, fa, hd):
                    rig.pose.bones[n].matrix_basis = snap[n]
                bpy.context.view_layer.update()
                sw = pose_for(s, fst[f], phi, rho, ds)
                row.append(max(0.0, sw - TARGET) * 4 + max(0.0, sw - HARD) * 40 + K_SW * sw + K_PHI * abs(phi)
                           + K_RHO * abs(rho) + K_SL * abs(ds) * 10); sws.append(sw)
            for n in (ua, fa, hd):
                rig.pose.bones[n].matrix_basis = snap[n]
            bpy.context.view_layer.update()
            cost.append(row); floor.append(min(sws))
        st = np.array(states, float)
        tr = K_CONT * (np.abs(st[:, None, 0] - st[None, :, 0]) + np.abs(st[:, None, 1] - st[None, :, 1])
                       + 1000 * np.abs(st[:, None, 2] - st[None, :, 2]))   # 1.5 cm slide step ~ a 15 deg turn
        cm = np.array(cost); acc = cm[0].copy(); back = []
        for t in range(1, len(frames)):
            tot = acc[:, None] + tr; b = tot.argmin(0); acc = tot[b, np.arange(len(states))] + cm[t]; back.append(b)
        j = int(acc.argmin()); path = [j]
        for b in reversed(back):
            j = int(b[j]); path.append(j)
        path = [states[i] for i in reversed(path)]
        keys, after = {}, []
        for f, (phi, rho, ds) in zip(frames, path):
            sc.frame_set(f)
            after.append(pose_for(s, fst[f], phi, rho, ds))
            keys[f] = {x: rig.pose.bones[x].matrix_basis.to_quaternion() for x in (ua, fa, hd)}
        prev = {}
        for f in frames:
            for x in (ua, fa, hd):
                pb = rig.pose.bones[x]; pb.rotation_mode = 'QUATERNION'; q = keys[f][x]
                if x in prev and q.dot(prev[x]) < 0:
                    q = -q
                prev[x] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        rep[f'{name}_{s}'] = {'swing_before': round(max(before), 1), 'swing_after': round(max(after), 1),
                              'best_possible': round(max(floor), 1),
                              'phi_range': [min(p[0] for p in path), max(p[0] for p in path)],
                              'rho_range': [min(p[1] for p in path), max(p[1] for p in path)],
                              'slide_range_mm': [round(1000 * min(p[2] for p in path)), round(1000 * max(p[2] for p in path))]}
        print('WRISTELBOW', name, s, json.dumps(rep[f'{name}_{s}']))
json.dump(rep, open(os.path.join(HERE, 'work', 'wrist_elbow.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
