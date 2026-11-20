"""Death and Dead from Meshy's dying_backwards (falls back, ends supine like native pmn2dea0-def0).
work/rig_v5.blend -> work/rig_v6.blend, actions 'Death' (35 frames at 24 fps, 1.42 s) and 'Dead' (held last pose).
 k0 idle carry pose -> k3 clip 9 (balance breaks) -> k34 clip 40 (lying; the clip's 0.4 s of standing before the fall
 is dropped and the fall runs at source speed; the engine lets a model death run past the native 625 ms).
The left arm is the clip's with a straight wrist. The staff is carried rigidly with the chest (Spine1) from its idle
carry placement, so it starts upright like the idle and ends lying along the right side (native: upright/out, raised
diagonally, low to the side); per frame the smallest grip lift-out / sagittal tilt / outward lean keeps it 15 mm off
the body and above the floor, and the right arm is solved onto it (elbow toward the clip's elbow). Afterwards run
smooth_attack.py on Death (SMOOTH_BLEND=rig_v6.blend SMOOTH_CLIP=Death SMOOTH_KEYS='[0, 3, 9, 16, 21, 25, 32]'
SMOOTH_LAST=33 SMOOTH_SIDES=Right SMOOTH_FLOOR=1): per-frame solves rolled the forearm up to 160 deg between frames. The lying body's lowest point rests on the floor, and no frame of the fall goes below it."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v5.blend'))
import staff_rig as sr

SRC = 'dying_backwards'
# k24 -> k34 (2026-10-10): the fall plays clip 9..40 at source speed (Meshy 24 fps) instead of ~1.45x; the engine
# finishes a longer death. smooth_attack.py keys for Death: [0, 3, 9, 16, 21, 25, 32], SMOOTH_LAST=33.
KEYS = [(0, ('idle', 0)), (3, ('clip', 9)), (34, ('clip', 40))]
LAST = KEYS[-1][0]
SPAN = (LAST - 3) / 21                                       # frame scale against the authored 24-frame clip
RIGHT, LEFT = sr.Side('Right'), sr.Side('Left')
idle = sr.sample_pose('Idle_9', 0)
clip = {f: sr.sample_pose(SRC, f) for f in range(9, 41)}
names = list(idle)


def source(k):
    for (k0, s0), (k1, s1) in zip(KEYS, KEYS[1:]):
        if k0 <= k <= k1:
            break
    if s0[0] == 'clip':
        c = s0[1] + (s1[1] - s0[1]) * (k - k0) / (k1 - k0); f = int(math.floor(c)); t = c - f
        a, b = clip[f], clip[min(f + 1, 40)]; w = 1.0
    else:
        t = (k - k0) / (k1 - k0); t = t * t * (3 - 2 * t); a, b = idle, clip[s1[1]]; w = t
    return {n: (a[n][0].slerp(b[n][0], t), a[n][1].lerp(b[n][1], t)) for n in names}, w


def lowest_body_z():
    dg = bpy.context.evaluated_depsgraph_get(); em = sr.mesh.evaluated_get(dg).to_mesh()
    z = min((sr.mesh.matrix_world @ v.co).z for v in em.vertices); sr.mesh.evaluated_get(dg).to_mesh_clear()
    return z


# floor: lying body at clip frame 40 (with straight wrists it does not change the body) rests on z = 0
sr.set_pose(clip[40]); bpy.context.view_layer.update()
DZ = -lowest_body_z()
print('FLOOR offset for the lying pose', round(DZ, 3))
for old in ('Dead', 'Death'):                          # Meshy's own 'Dead' death clip keeps its data under a new name
    if old in bpy.data.actions:
        bpy.data.actions[old].name = old + '_meshy'
sr.set_pose(idle)
IDLE_CHEST = (sr.AW @ sr.B('Spine1').matrix).copy()
Mh = sr.AW @ sr.B('RightHand').matrix
IDLE_G = Mh.translation + Mh.to_3x3() @ RIGHT.grip_hand; IDLE_A = (Mh.to_3x3() @ RIGHT.axis_hand).normalized()
_, IDLE_F, IDLE_R = sr.body_frame()
phi_prev = None; prev_adj = None
act = bpy.data.actions.new('Death'); act.use_fake_user = True
sr.arm.animation_data.action = act
rows = []
for k in range(0, LAST + 1):
    pose, w = source(k)
    sr.set_pose(pose)
    fall = max(0.0, min(1.0, (k - 3) / (12 * SPAN)))                # floor offset fades in while falling
    hb = sr.B('Hips'); M = sr.AW @ hb.matrix; M.translation.z += DZ * fall; hb.matrix = sr.AW.inverted() @ M
    bpy.context.view_layer.update()
    # left wrist straight (fist); right arm solved onto the staff carried rigidly with the chest
    fa = sr.B('LeftForeArm'); hb_ = sr.B('LeftHand')
    Rn = (sr.AW @ fa.matrix).to_3x3() @ LEFT.rel['Hand']
    cur = (sr.AW @ hb_.matrix).to_3x3().to_quaternion()
    sr._set_world('LeftHand', cur.slerp(Rn.to_quaternion(), w).to_matrix(), sr.AW @ hb_.head, None)
    T = (sr.AW @ sr.B('Spine1').matrix) @ IDLE_CHEST.inverted()
    G0 = T @ IDLE_G; a0 = (T.to_3x3() @ IDLE_A).normalized()
    Pb = sr.body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm', 'mixamorig:RightArm'))
    side_axis = (T.to_3x3() @ IDLE_R).normalized(); fwd_axis = (T.to_3x3() @ IDLE_F).normalized()
    cands = []
    for dout in (0.0, 0.06, 0.12, 0.2):                      # lift the grip out from the body
        for dtilt in (0, -10, 10, -20, 20):                  # tilt the staff in the body's sagittal plane
            for droll in (0, 10, 20):                        # lean the staff foot outward
                a = (Quaternion(side_axis, math.radians(dtilt)) @ Quaternion(fwd_axis, math.radians(-droll)) @ a0).normalized()
                G = G0 + side_axis * dout
                low = min((G - a * sr.GRIP_FROM_FOOT).z, (G + a * (sr.L - sr.GRIP_FROM_FOOT)).z)
                if low < 0.015:
                    G = G + Vector((0, 0, 0.015 - low))
                clr = sr.shaft_clearance(Pb, G, a, below_grip=sr.GRIP_FROM_FOOT, above_grip=sr.L - sr.GRIP_FROM_FOOT, radius=0.03)
                adj = (dout, dtilt, droll)
                change = dout * 100 + abs(dtilt) * 0.3 + droll * 0.3 + (G - G0).length * 100
                if prev_adj is not None:
                    change += 0.6 * (abs(dout - prev_adj[0]) * 100 + abs(dtilt - prev_adj[1]) + abs(droll - prev_adj[2]))
                cands.append((clr < 0.015, change if clr >= 0.015 else -clr, G, a, clr, adj))
    cands.sort(key=lambda c: (c[0], c[1]))
    pole = (sr.AW @ sr.B('RightForeArm').head) - ((sr.AW @ sr.B('RightArm').head) + G0) * 0.5
    best = None
    for bad, change, G, a, clr, adj in cands[:12]:          # arm solve on the cheapest clear candidates
        r = RIGHT.search([(G, a, adj)], pole, phi_prev)
        Ga = r['W'] + r['Rh'] @ RIGHT.grip_hand; aa = (r['Rh'] @ RIGHT.axis_hand).normalized()   # where it really lands
        low = min((Ga - aa * sr.GRIP_FROM_FOOT).z, (Ga + aa * (sr.L - sr.GRIP_FROM_FOOT)).z)
        cost = r['cost'] + change * 2 + (1000 if bad else 0) + max(0.0, 0.01 - low) * 20000
        if best is None or cost < best[0]:
            best = (cost, r, clr, adj)
    _, r, clr, adj = best; phi_prev = r['phi']; prev_adj = adj
    for bn, R3, head in (('Arm', r['Ra'], r['S']), ('ForeArm', r['Rf'], r['E']), ('Hand', r['Rh'], r['W'])):
        sr._set_world('Right' + bn, R3, head, None)
    lowz = lowest_body_z()                                 # no part of the body below the floor while falling
    if lowz < 0:
        hb = sr.B('Hips'); M = sr.AW @ hb.matrix; M.translation.z -= lowz; hb.matrix = sr.AW.inverted() @ M
        bpy.context.view_layer.update()
    sr.key_all(k)
    Mh = sr.AW @ sr.B('RightHand').matrix
    G = Mh.translation + Mh.to_3x3() @ RIGHT.grip_hand; a = (Mh.to_3x3() @ RIGHT.axis_hand).normalized()
    Pb = sr.body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm'))
    q = ((sr.AW @ sr.B('RightForeArm').matrix).to_3x3().inverted() @ Mh.to_3x3()).to_quaternion()
    row = {'k': k, 'adjust': adj, 'r_swing': round(r['sw'], 1), 'r_twist': round(r['tw'], 1), 'staff_low_z': round(min((G - a * sr.GRIP_FROM_FOOT).z, (G + a * (sr.L - sr.GRIP_FROM_FOOT)).z), 3),
           'staff_clearance_mm': round(1000 * sr.shaft_clearance(Pb, G, a, below_grip=sr.GRIP_FROM_FOOT, above_grip=sr.L - sr.GRIP_FROM_FOOT, radius=0.03), 1),
           'wrist_deg': round(math.degrees(q.angle), 1), 'body_low_z': round(lowest_body_z(), 3)}
    rows.append(row); print('DEATH', row)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, LAST
dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True
sr.arm.animation_data.action = dead
sr.key_all(0); sr.key_all(1)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 1
json.dump(rows, open(os.path.join(common.WORK, 'death_report.json'), 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v6.blend'))
