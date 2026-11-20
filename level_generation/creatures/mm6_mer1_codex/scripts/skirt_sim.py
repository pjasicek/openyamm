"""Bake the cloak chains (cloak_rig.py) into every clip of a work blend (in place). Args: blend [clip ...].

Per chain point (8 below each root: joints and bone midpoints, 17 chains): verlet with velocity damping DAMP per substep (SUB substeps per
24 fps frame); a pull (STIFF per substep) toward the rest bell hung from the chain root with the chest's heading only
(yaw), so the cloak hangs plumb when the body leans, blending into the chest's own frame as the chest tilts past
25-70 deg and down onto the floor (the death fall: the cloak falls with him and lies spread flat); exact segment lengths; neighbour chains kept between 0.6 and
NB_MAX x their rest spacing; collisions last in each of 3 constraint iterations (spacing last pulled pushed chains
back into the legs: 1,295 poking leg vertices in the run); one-sided collision capsules (a point inside moves outward along its chain's direction) (thighs, shins, hips, torso, upper arms, forearms; radius + MARGIN for
the cloth's half thickness, each radius shrunk so no rest point starts inside, arms not below 4 cm); floor z >= FLOOR. Chain roots ride
on the chest bone 'B_Pelvis'. Loops ('Standing', 'Walking', 'Running', 'Fidget') simulate three cycles and keep the last
(seamless); one-shots pre-roll PRE frames on their first pose; 'Dead' is the settled end of 'Death' (held 24 more
frames). Each chain bone is then aimed at the next simulated point and keyed (quaternion) on every clip frame."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, args[0]))
scene = bpy.context.scene; scene.render.fps = 30
arm = bpy.data.objects['Rig']; AW = arm.matrix_world.copy(); AWI = AW.inverted()
CH = json.loads(scene['merchant_skirt'])
SUB, DAMP, STIFF, MARGIN, FLOOR, PRE = 6, 0.985, 0.04, 0.02, 0.015, 30
NB_MAX = 1.06               # neighbour chains: at most 6 % wider apart than at rest (1.12 let the hem open 11-16 cm)
LOOPS = {'Standing', 'Walking', 'Running', 'Fidget'}
CLIPS = args[1:] or [n for n in ('Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget', 'Attack')
                     if n in bpy.data.actions]
order = sorted(range(len(CH)), key=lambda i: CH[i]['deg'])
# 9 points per chain: the 5 bone joints and each bone's midpoint (collisions act on points; a bone is a straight
# 26 cm segment, so the shin slipped between its ends: 1,802 poking leg vertices over the walk)
REST = []
for c in CH:
    J = np.array(c['pts']); F = []
    for k in range(4):
        F += [J[k], (J[k] + J[k + 1]) / 2]
    F.append(J[4]); REST.append(np.array(F))
NP = len(REST[0])
# outward direction of each chain (rest, horizontal, from the body axis): collisions push only this way, so a leg
# sweeping through a chain point cannot push it to the inside of the cloak (it did: points ended in front of the
# back leg)
AXIS = np.array([0.0, 0.015, 0.0])
OUT = []
for c in CH:
    a = math.radians(c['deg']); OUT.append(np.array([math.sin(a), math.cos(a), 0.0]))
STEPS = np.arange(0.0, 0.45, 0.004)
CAPS = [('B_L_Thigh','B_L_Calf',.13),('B_R_Thigh','B_R_Calf',.13),('B_L_Calf','B_L_Foot',.13),('B_R_Calf','B_R_Foot',.13),('B_L_Thigh','B_R_Thigh',.12),('B_L_Foot','B_L_Toe0',.09),('B_R_Foot','B_R_Toe0',.09)]
# feet: the run's heel kicked up through the back hem; arms: radius floor 4 cm below (the side chains rest against them)


def set_action(act):
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]


def fcurves(act):
    out = list(getattr(act, 'fcurves', []) or [])
    if not out and hasattr(act, 'layers'):
        out = [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return out


def strip_cloak(act):
    for l in getattr(act, 'layers', []):
        for s in l.strips:
            for cb in s.channelbags:
                for fc in list(cb.fcurves):
                    if '"Cloak_' in fc.data_path:
                        cb.fcurves.remove(fc)
    if hasattr(act, 'fcurves'):
        for fc in list(act.fcurves):
            if '"Cloak_' in fc.data_path:
                act.fcurves.remove(fc)


def body_state(t):
    scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    sp = arm.pose.bones['B_Pelvis'].matrix.copy()
    caps = [(np.array(arm.pose.bones[a].head), np.array(arm.pose.bones[b].head)) for a, b, r in CAPS]
    return sp, caps


rest_sp = arm.data.bones['B_Pelvis'].matrix_local.copy()
rest_caps = [(np.array(arm.data.bones[a].head_local), np.array(arm.data.bones[b].head_local)) for a, b, r in CAPS]


def seg_dist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    q = a + np.outer(t, ab) if p.ndim == 2 else a + t * ab
    return p - q


radii = []
allrest = np.vstack([r[1:] for r in REST])
for (a, b), (na, _, r) in zip(rest_caps, CAPS):
    d = np.linalg.norm(seg_dist(allrest, a, b), axis=1).min()
    floor_r = .07  # shrunk 1-2 cm arm capsules let the elbows through
    radii.append(max(floor_r,r))
print('CAPSULE radii', [round(x, 3) for x in radii])


def yaw_rot(sp):
    f = sp.to_3x3() @ rest_sp.to_3x3().inverted() @ Vector((0, -1, 0))
    a = math.atan2(f.x, -f.y)
    return np.array(Matrix.Rotation(a, 3, 'Z'))


def tilt_w(sp):
    """0 while the chest is upright, 1 once it tilts 70 deg (lying): the cloak target follows the chest frame."""
    up = (sp.to_3x3() @ rest_sp.to_3x3().inverted()) @ Vector((0, 0, 1))
    t = math.degrees(up.angle(Vector((0, 0, 1))))
    x = min(1.0, max(0.0, (t - 25.0) / 45.0))
    return x * x * (3 - 2 * x)


def roots(sp):
    M = sp @ rest_sp.inverted()
    return [np.array(M @ Vector(r[0])) for r in REST]


def simulate(act, mode):
    stiff = STIFF * (4.0 if act.name == 'Death' else 1.0)    # no lagging sheets while he falls
    f0, f1 = (int(round(x)) for x in act.frame_range)
    n = f1 - f0
    if mode == 'loop':                                   # three cycles; the clip's last frame closes the cycle
        times = [f0 + (i % n) for i in range(3 * n)] + [f1]
        keep_from = 2 * n
    else:
        times = [f0] * PRE + list(range(f0, f1 + 1)) + ([f1] * 24 if mode == 'settle' else [])
        keep_from = PRE
    sp, caps = body_state(times[0])
    R0 = roots(sp); Ry = yaw_rot(sp)
    X = [np.array([R0[c] + Ry @ (REST[c][k] - REST[c][0]) for k in range(NP)]) for c in range(len(CH))]
    V = [np.zeros_like(x) for x in X]
    seglen = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in REST]
    nb = [(order[i], order[i + 1]) for i in range(len(order) - 1)] + [(order[-1],order[0])]
    nbrest = {(a, b): np.linalg.norm(REST[a][1:] - REST[b][1:], axis=1) for a, b in nb}
    prev = (sp, caps)
    out = []
    for step, t in enumerate(times):
        cur = body_state(t)
        for s in range(SUB):
            w = (s + 1) / SUB                             # body interpolated between frames
            M0, M1 = prev[0], cur[0]
            q = M0.to_quaternion().slerp(M1.to_quaternion(), w); tr = M0.translation.lerp(M1.translation, w)
            sp = Matrix.Translation(tr) @ q.to_matrix().to_4x4()
            caps = [(a0 + (a1 - a0) * w, b0 + (b1 - b0) * w) for (a0, b0), (a1, b1) in zip(prev[1], cur[1])]
            Rr = roots(sp); Ry = yaw_rot(sp); tw = tilt_w(sp)
            Mc = sp @ rest_sp.inverted()
            old = [x.copy() for x in X]
            for c in range(len(CH)):
                x = X[c]
                tgt = np.array([Rr[c] + Ry @ (REST[c][k] - REST[c][0]) for k in range(NP)])
                if tw > 0:
                    tgt = tgt * (1 - tw) + np.array([tuple(Mc @ Vector(REST[c][k])) for k in range(NP)]) * tw
                    # lying: the cloak spreads flat on the floor around him (as the native corpse) instead of
                    # standing up as a bell (the death crumpled with 34x edge stretch)
                    tgt[1:, 2] = np.maximum(tgt[1:, 2],FLOOR)
                x[1:] += V[c][1:] * DAMP + (tgt[1:] - x[1:]) * stiff
                x[0] = Rr[c]
            # constraints iterated together: lengths, neighbour spacing, one-sided collisions and floor (collisions
            # alone pushed neighbouring chains apart at the back hem: 12-16 cm openings in the walk and run)
            for it in range(3):
                for c in range(len(CH)):
                    x = X[c]
                    for k in range(NP - 1):               # segment lengths, from the root down
                        d = x[k + 1] - x[k]; L = np.linalg.norm(d)
                        x[k + 1] = x[k] + d / max(L, 1e-9) * seglen[c][k]
                for a, b in nb:                           # neighbour spacing
                    d = X[b][1:] - X[a][1:]; L = np.linalg.norm(d, axis=1); r = nbrest[(a, b)]
                    corr = np.where(L > NB_MAX * r, L - NB_MAX * r, np.where(L < 0.6 * r, L - 0.6 * r, 0.0))
                    u = d / np.maximum(L, 1e-9)[:, None]
                    X[a][1:] += u * (corr * 0.5)[:, None]; X[b][1:] -= u * (corr * 0.5)[:, None]
                for c in range(len(CH)):                  # one-sided collisions (outward only) and floor
                    x = X[c]; u = (1-tw)*(Ry @ OUT[c]) + tw*(np.array(Mc.to_3x3()) @ OUT[c]); u /= max(np.linalg.norm(u),1e-9)
                    for (a, b), r in zip(caps, radii):
                        d = seg_dist(x[1:], a, b); L = np.linalg.norm(d, axis=1)
                        for j in np.where(L < r + MARGIN)[0]:
                            q = x[1 + j]
                            for st in STEPS:              # first clear position along the chain's outward direction
                                if np.linalg.norm(seg_dist(q + u * st, a, b)) >= r + MARGIN:
                                    break
                            x[1 + j] = q + u * st
                    x[1:, 2] = np.maximum(x[1:, 2], FLOOR)
            for c in range(len(CH)):
                V[c] = X[c] - old[c]
        prev = cur
        if step >= keep_from:
            out.append((t, [x.copy() for x in X], cur[0].copy()))
    return out


L_rest = {}
for c in CH:
    par = 'B_Pelvis'
    for b in c['bones']:
        L_rest[b] = arm.data.bones[par].matrix_local.inverted() @ arm.data.bones[b].matrix_local
        par = b


def key_frame(frame, X, sp):
    for c, x in zip(CH, X):
        Mp = sp
        for k, b in enumerate(c['bones']):
            Mu = Mp @ L_rest[b]
            y = Mu.to_3x3() @ Vector((0, 1, 0)); d = Vector(x[2 * k + 2]) - Mu.translation
            R = y.rotation_difference(d.normalized()).to_matrix()
            Md = (R @ Mu.to_3x3()).to_4x4(); Md.translation = Mu.translation
            pb = arm.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = (Mu.inverted() @ Md).to_quaternion()
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            Mp = Md


report = {}
for name in CLIPS:
    act = bpy.data.actions[name]
    strip_cloak(act); set_action(act)
    for c in CH:
        for b in c['bones']:
            arm.pose.bones[b].rotation_mode = 'QUATERNION'; arm.pose.bones[b].rotation_quaternion = Quaternion()
    mode = 'loop' if name in LOOPS else ('settle' if name == 'Death' else 'once')
    res = simulate(act, mode)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames = {}
    for t, X, sp in res:
        frames.setdefault(int(t), (X, sp))               # one-shot: first visit of each frame
    if mode == 'loop':
        frames = {int(t): (X, sp) for t, X, sp in res}
    for f in range(f0, f1 + 1):
        X, sp = frames[f]
        key_frame(f, X, sp)
    if name == 'Death' and 'Dead' in bpy.data.actions:
        X, sp = res[-1][1], res[-1][2]
        dead = bpy.data.actions['Dead']; strip_cloak(dead); set_action(dead)
        for f in (0, 1):
            key_frame(f, X, sp)
        set_action(act)
    disp = max(float(np.linalg.norm(X[c][1:] - REST[c][1:], axis=1).max()) for X, sp in [frames[f1]] for c in range(len(CH)))
    report[name] = round(disp, 3)
    print('CLOAK', name, mode, 'frames', f1 - f0 + 1, 'max displacement at the last frame', report[name])
# the cloak lies under the fallen body: lift Death/Dead so no vertex is more than 1 cm below the floor
mesh = bpy.data.objects['Body']
for name in ('Death', 'Dead'):
    if name not in bpy.data.actions or ('Death' not in CLIPS):
        continue
    act = bpy.data.actions[name]; set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    hips = arm.pose.bones['B_Pelvis']; mats = []; worst = 0.0
    for f in np.arange(f0, f1 + .001, .5):
        scene.frame_set(int(f),subframe=float(f%1))
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        low = min((mesh.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear()
        worst = min(worst, low)
        mats.append((f, Matrix.Translation((0, 0, .004 - low)) @ hips.matrix))
    for f, M in mats:
        scene.frame_set(int(f),subframe=float(f%1)); hips.matrix = M; hips.keyframe_insert('location', frame=float(f))
    print('FLOOR', name, 'lowest vertex after the cloak bake', round(worst, 3))
set_action(bpy.data.actions['Standing'])
bpy.ops.wm.save_mainfile()
