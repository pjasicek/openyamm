"""Polish for the candidate attacks (after cand_blade_clear.py), as polish_motion.py and final_fit.py do for the bound
clips, without smoothing the library arms:
- upper-arm counter-twist: one gain per clip and side (0, .25, .5, .75, 1 of the upper arm's roll) chosen by the arm
  skin's p99 edge stretch on every other frame; forearm twist re-derived at 0.6 of the hand roll;
- pauldrons and head: where a pauldron plate is inside the head or neck skin (signed nearest face, deeper than TOL),
  the pauldron's follow of the upper arm is scaled down (.75 .. 0) until it clears, then if needed the head tilts away
  from that shoulder (3 .. 12 deg about the chest's forward axis); Gaussian-smoothed, never below a frame's need.
Args: -- <in blend> <out blend>   (env TOL 0.002)"""
from pathlib import Path
import sys, os, json, math
import bpy, numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts')); import armik
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
TOL = float(os.environ.get('TOL', '0.002'))
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
GI = {g.index: g.name for g in body.vertex_groups}
DOM = [GI[max(v.groups, key=lambda x: x.weight).group] if v.groups else '' for v in body.data.vertices]
HEADF = [tuple(f.vertices) for f in body.data.polygons if all(DOM[i] in ('B_Head', 'B_Neck', 'Bone_025', 'headfront') for i in f.vertices)]
base = np.array([v.co[:] for v in body.data.vertices]); edges = np.array([e.vertices[:] for e in body.data.edges])
L0 = np.linalg.norm(base[edges[:, 0]] - base[edges[:, 1]], axis=1)
armm = {s: np.array([sum(g.weight for g in v.groups if GI[g.group].startswith(f'B_{s}_') and any(x in GI[g.group] for x in ('UpperArm', 'Forearm'))) > .3 for v in body.data.vertices]) for s in 'LR'}
EF = {s: armm[s][edges[:, 0]] & armm[s][edges[:, 1]] for s in 'LR'}
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
GAINS = [0., .25, .5, .75, 1.]


def ev(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = e.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(o.matrix_world.to_3x3()).T + np.array(o.matrix_world.translation)


def ua_axis(s):
    ub = rig.data.bones[f'B_{s}_UpperArm']; fb = rig.data.bones[f'B_{s}_Forearm']
    return (ub.matrix_local.inverted() @ fb.head_local).normalized()


def set_twists(s, gain):
    ax = ua_axis(s); _, tw = armik.split_swing_twist(rig.pose.bones[f'B_{s}_UpperArm'].matrix_basis.to_quaternion(), ax)
    pb = rig.pose.bones[f'B_{s}_UpperArmTwist']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(ax, -gain * tw)
    fb = rig.data.bones[f'B_{s}_Forearm']; hb = rig.data.bones[f'B_{s}_Hand']; ax = (fb.matrix_local.inverted() @ hb.head_local).normalized()
    rel = (rig.pose.bones[fb.name].matrix.inverted() @ rig.pose.bones[hb.name].matrix).to_quaternion(); rest = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
    _, tw = armik.split_swing_twist(rel @ rest.inverted(), ax)
    pb = rig.pose.bones[f'B_{s}_ForearmTwist']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(ax, .6 * tw)


def head_depth(s):
    t = BVHTree.FromPolygons(ev(body).tolist(), HEADF); worst = 0.0
    for p in ev(bpy.data.objects[f'Arm_pauldron_{s}']):
        loc, nrm, _, d = t.find_nearest(Vector(p), .08)
        if loc is not None and d > TOL and (Vector(p) - loc).dot(nrm) < -.5 * d: worst = max(worst, d)
    return worst


report = {}
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; n = int(act.frame_range[1])
    score = {s: np.zeros(len(GAINS)) for s in 'LR'}
    for f in range(0, n + 1, 2):
        sc.frame_set(f)
        for s in 'LR':
            for i, g in enumerate(GAINS):
                set_twists(s, g); bpy.context.view_layer.update(); C = ev(body) @ np.linalg.inv(np.array(body.matrix_world.to_3x3())).T
                r_ = np.linalg.norm(C[edges[:, 0]] - C[edges[:, 1]], axis=1) / np.maximum(L0, 1e-6)
                score[s][i] = max(score[s][i], float(np.percentile(r_[EF[s]], 99)))
    gain = {s: GAINS[int(np.argmin(score[s]))] for s in 'LR'}
    # pauldrons and head
    pscale = {s: np.ones(n + 1) for s in 'LR'}; htilt = {s: np.zeros(n + 1) for s in 'LR'}; before = {s: 0.0 for s in 'LR'}
    for f in range(n + 1):
        sc.frame_set(f)
        for s in 'LR': set_twists(s, gain[s])
        bpy.context.view_layer.update()
        for s, sg in (('L', 1), ('R', -1)):
            d0 = head_depth(s); before[s] = max(before[s], d0)
            if d0 == 0: continue
            pb = rig.pose.bones[f'B_{s}_Pauldron']; q0 = pb.rotation_quaternion.copy(); done = False
            for k in (.75, .5, .25, 0.):
                pb.rotation_quaternion = Quaternion().slerp(q0, k); bpy.context.view_layer.update()
                if head_depth(s) == 0: pscale[s][f] = k; done = True; break
            if not done:
                pscale[s][f] = 0.; hb = rig.pose.bones['B_Head']; h0 = hb.rotation_quaternion.copy()
                for deg in (3, 6, 9, 12):
                    fwd = (armik.W(rig, 'B_Spine2').to_3x3() @ CHEST_FWD).normalized(); M = armik.W(rig, 'B_Head')
                    armik.set_world(rig, 'B_Head', armik.rot_world(M, Matrix.Rotation(math.radians(sg * deg), 3, fwd) @ M.to_3x3().normalized()))
                    ok = head_depth(s) == 0; hb.rotation_quaternion = h0; bpy.context.view_layer.update()
                    if ok: htilt[s][f] = deg; break
                else:
                    htilt[s][f] = 12
            pb.rotation_quaternion = q0; bpy.context.view_layer.update()
    r = 4; kern = np.exp(-.5 * (np.arange(-r, r + 1) / 1.5) ** 2); kern /= kern.sum()
    for s in 'LR':
        sm = np.convolve(np.pad(1 - pscale[s], r, mode='edge'), kern, mode='valid'); pscale[s] = 1 - np.maximum(sm, 1 - pscale[s])
        sm = np.convolve(np.pad(htilt[s], r, mode='edge'), kern, mode='valid'); htilt[s] = np.maximum(sm, htilt[s])
    for f in range(n + 1):
        sc.frame_set(f)
        for s, sg in (('L', 1), ('R', -1)):
            set_twists(s, gain[s]); pb = rig.pose.bones[f'B_{s}_Pauldron']; pb.rotation_quaternion = Quaternion().slerp(pb.rotation_quaternion.copy(), float(pscale[s][f]))
            if htilt[s][f] > .05:
                bpy.context.view_layer.update(); fwd = (armik.W(rig, 'B_Spine2').to_3x3() @ CHEST_FWD).normalized(); M = armik.W(rig, 'B_Head')
                armik.set_world(rig, 'B_Head', armik.rot_world(M, Matrix.Rotation(math.radians(sg * float(htilt[s][f])), 3, fwd) @ M.to_3x3().normalized()))
        bpy.context.view_layer.update()
        for b in ('B_L_UpperArmTwist', 'B_R_UpperArmTwist', 'B_L_ForearmTwist', 'B_R_ForearmTwist', 'B_L_Pauldron', 'B_R_Pauldron', 'B_Head'):
            rig.pose.bones[b].keyframe_insert('rotation_quaternion', frame=f)
    report[act.name] = {'upper_twist_gain': gain, 'arm_p99_by_gain': {s: [round(x, 3) for x in score[s]] for s in 'LR'},
                        'pauldron_head_depth_before_cm': {s: round(before[s] * 100, 2) for s in 'LR'},
                        'min_pauldron_follow': {s: round(float(pscale[s].min()), 2) for s in 'LR'}, 'max_head_tilt_deg': {s: round(float(htilt[s].max()), 1) for s in 'LR'}}
    print('POLISH', act.name, json.dumps(report[act.name]), flush=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
(P / 'review/cand_polish.json').write_text(json.dumps(report, indent=2) + '\n')
