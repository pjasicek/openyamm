"""Planted feet stay planted in the candidate attacks (after cand_fit.py). The in-place library clips drift their feet
(their root travel was taken out), the reduced Mixamo travel and the eases from and to Standing slide them too.
Per foot and frame, on the skinned mesh: the foot vertices within CONTACT of the floor on two consecutive frames are
the contact; their 10th-percentile horizontal motion is the slide (a pivot on the ball turns the far claws, not the
pivot, so pivots are kept). The slide accumulates while the foot stays in contact and is taken back out by two-bone IK
on the ankle (foot rotation kept); when the foot lifts, the correction fades over FADE frames, and over the clip's last
blend_out seconds it fades to zero so the clip still ends exactly on Standing. Capped at CAP m. A clip with
`footlock: false` (the run strike, played while the actor dashes) is left alone.
Then the eases from and to Standing: where a foot still slides in them (the source stance is not Standing's, so the
foot travels between the two while touching the floor: up to 6 cm a frame), it steps instead. Each run of sliding
frames (contact slide > STEP_SLIDE m a frame), widened by a frame either side, lifts the ankle on a sine arc of
0.4 x its travel (STEP_MIN .. STEP_MAX m), by the same two-bone IK.
Args: -- <in blend> <out blend> <config json>   (env CONTACT 0.012, FADE 5, CAP 0.2, STEP_SLIDE 0.008, STEP_MIN 0.03,
STEP_MAX 0.1)"""
from pathlib import Path
import sys, os, json, math
import bpy, numpy as np
from mathutils import Vector
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts')); import armik
src, out, cfgp = sys.argv[sys.argv.index('--') + 1:][:3]
CONTACT, FADE, CAP = float(os.environ.get('CONTACT', '0.012')), int(os.environ.get('FADE', '5')), float(os.environ.get('CAP', '0.2'))
STEP_SLIDE, STEP_MIN, STEP_MAX = (float(os.environ.get(k, d)) for k, d in (('STEP_SLIDE', '0.008'), ('STEP_MIN', '0.03'), ('STEP_MAX', '0.1')))
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
CFG = {'Harrower_' + c['name']: c for c in json.loads(Path(cfgp).read_text())}
VG = [g.name for g in body.vertex_groups]
FOOT = {s: np.array([sum(e.weight for e in v.groups if VG[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > .5 for v in body.data.vertices]) for s in 'LR'}
LEG = {s: (f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot') for s in 'LR'}


def feet():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3) @ np.array(body.matrix_world.to_3x3()).T + np.array(body.matrix_world.translation)
    return {s: co[FOOT[s]] for s in 'LR'}


def two_bone(s, target):
    th, ca, ft = LEG[s]; Rf = armik.W(rig, ft).to_3x3().normalized()
    H, K, A = armik.W(rig, th).translation, armik.W(rig, ca).translation, armik.W(rig, ft).translation
    L1, L2 = (K - H).length, (A - K).length; d = target - H; dist = min(d.length, (L1 + L2) * 0.999)
    u = d.normalized(); pole = (K - H) - u * (K - H).dot(u); pole = pole.normalized() if pole.length > 1e-6 else Vector((0, -1, 0))
    c = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    Kn = H + L1 * (u * c + pole * math.sqrt(max(0.0, 1 - c * c)))
    M = armik.W(rig, th); armik.set_world(rig, th, armik.rot_world(M, (K - H).normalized().rotation_difference((Kn - H).normalized()).to_matrix() @ M.to_3x3().normalized()))
    M = armik.W(rig, ca); A2 = armik.W(rig, ft).translation
    q = (A2 - M.translation).normalized().rotation_difference((H + u * dist - M.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(M, q.to_matrix() @ M.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), Rf))


report = {}
for name, c in CFG.items():
    if not c.get('footlock', True): continue
    act = bpy.data.actions[name]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; n = int(act.frame_range[1])
    F = []
    for f in range(n + 1):
        sc.frame_set(f); F.append(feet())
    corr = {s: np.zeros((n + 1, 2)) for s in 'LR'}; slid = {s: 0.0 for s in 'LR'}
    for s in 'LR':
        D = np.zeros(2); since = 99
        for i in range(1, n + 1):
            A_, B_ = F[i - 1][s], F[i][s]; m = (A_[:, 2] < CONTACT) & (B_[:, 2] < CONTACT)
            if m.sum() >= 3:
                v = (B_[m] - A_[m])[:, :2]; mag = np.linalg.norm(v, axis=1); k = int(np.argsort(mag)[max(0, int(.1 * len(mag)) - 1)])
                D = D + v[k]; slid[s] += float(mag[k]); since = 0
            else:
                since += 1; D = D * max(0.0, 1 - 1.0 / FADE) if since <= FADE else np.zeros(2)
            L = np.linalg.norm(D)
            if L > CAP: D = D * (CAP / L)
            corr[s][i] = -D
    bo = float(c.get('blend_out', .25)); T = n / 30.0
    for i in range(n + 1):
        w = min(1.0, max(0.0, (T - i / 30.0) / bo)); w = w * w * (3 - 2 * w)
        for s in 'LR': corr[s][i] *= w
    keys = {}
    for i in range(n + 1):
        if not any(np.linalg.norm(corr[s][i]) > 1e-4 for s in 'LR'): continue
        sc.frame_set(i)
        for s in 'LR':
            v = corr[s][i]
            if np.linalg.norm(v) > 1e-4: two_bone(s, armik.W(rig, LEG[s][2]).translation + Vector((v[0], v[1], 0)))
        keys[i] = {b: rig.pose.bones[b].rotation_quaternion.copy() for s in 'LR' for b in LEG[s]}
    for i, kv in keys.items():
        for b, q in kv.items():
            pb = rig.pose.bones[b]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=i)
    # the eases: a foot that still slides steps
    F = []
    for f in range(n + 1):
        sc.frame_set(f); F.append(feet())
    ease = set(range(0, int(round(float(c.get('blend_in', .1)) * 30)) + 3)) | set(range(n - int(round(bo * 30)) - 2, n + 1))
    steps = {s: [] for s in 'LR'}; lift = {s: np.zeros(n + 1) for s in 'LR'}
    for s in 'LR':
        slide = np.zeros(n + 1)
        for i in range(1, n + 1):
            A_, B_ = F[i - 1][s], F[i][s]; m = (A_[:, 2] < CONTACT) & (B_[:, 2] < CONTACT)
            if m.sum() >= 3: slide[i] = np.percentile(np.linalg.norm((B_[m] - A_[m])[:, :2], axis=1), 10)
        bad = [i for i in range(1, n + 1) if slide[i] > STEP_SLIDE and i in ease]
        runs = []
        for i in bad:   # widened by a frame either side (the slide of frame i is from i - 1); touching runs are one step
            a_, b_ = max(0, i - 2), min(n, i + 1)
            if runs and a_ <= runs[-1][1]: runs[-1][1] = b_
            else: runs.append([a_, b_])
        for a_, b_ in runs:
            travel = float(np.linalg.norm(np.median(F[b_][s], 0)[:2] - np.median(F[a_][s], 0)[:2]))
            h = min(STEP_MAX, max(STEP_MIN, .4 * travel))
            for i in range(a_, b_ + 1): lift[s][i] = max(lift[s][i], h * math.sin(math.pi * (i - a_) / max(1, b_ - a_)))
            steps[s].append({'frames': [a_, b_], 'travel_cm': round(travel * 100, 1), 'lift_cm': round(h * 100, 1)})
    keys = {}
    for i in range(n + 1):
        if not any(lift[s][i] > 1e-4 for s in 'LR'): continue
        sc.frame_set(i)
        for s in 'LR':
            if lift[s][i] > 1e-4: two_bone(s, armik.W(rig, LEG[s][2]).translation + Vector((0, 0, lift[s][i])))
        keys[i] = {b: rig.pose.bones[b].rotation_quaternion.copy() for s in 'LR' if lift[s][i] > 1e-4 for b in LEG[s]}
    for i, kv in keys.items():
        for b, q in kv.items():
            pb = rig.pose.bones[b]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=i)
    report[name] = {'source_slide_cm': {s: round(slid[s] * 100, 1) for s in 'LR'}, 'max_correction_cm': {s: round(float(np.linalg.norm(corr[s], axis=1).max()) * 100, 1) for s in 'LR'},
                    'ease_steps': steps}
    print('FOOTLOCK', name, json.dumps(report[name]), flush=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
(P / 'review/cand_footlock.json').write_text(json.dumps(report, indent=2) + '\n')
