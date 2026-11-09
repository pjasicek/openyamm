"""Arms clear of the torso plates in the candidate attacks (after cand_footlock.py, before the blade clearance). The
library arms cross a slimmer chest: the armour gate found upper-arm skin in the chest plate, a forearm through the belt
and the forearm guard in the other thigh. Per frame and side: the arm's skin (weight > ARMW on the upper arm, forearm
and their twist bones; 0.6 reaches the deltoid, where the chest plate met the shoulder) and its forearm plate against the chest, belt and spine plates and the other thigh's skin
(signed nearest face within REACH, inside when (p - q) . n < -0.5 d, deeper than TOL; the thigh is an open patch, so
a point far behind it reads as inside: REACH keeps the test to real penetrations). Where an arm is inside, the upper arm turns
out about the chest's forward axis by the smallest extra angle (STEP .. MAX deg) that clears it (the arm points are
turned rigidly about the shoulder for the search); the angles are Gaussian-smoothed (never below a frame's need) and
keyed on the upper arm. Args: -- <in blend> <out blend>   (env TOL 0.002, STEP 3, MAX 24, REACH 0.04, ARMW 0.6)"""
from pathlib import Path
import sys, os, json, math
import bpy, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts')); import armik
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
TOL, STEP, MAXD = float(os.environ.get('TOL', '0.002')), float(os.environ.get('STEP', '3')), float(os.environ.get('MAX', '24'))
REACH = float(os.environ.get('REACH', '0.04')); ARMW = float(os.environ.get('ARMW', '0.6'))
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
GI = {g.index: g.name for g in body.vertex_groups}
W = {}
for v in body.data.vertices:
    for g in v.groups: W.setdefault(GI[g.group], np.zeros(len(body.data.vertices)))[v.index] = g.weight
DOM = [GI[max(v.groups, key=lambda x: x.weight).group] if v.groups else '' for v in body.data.vertices]
ARMV = {s: np.where(sum(W.get(f'B_{s}_{b}', 0) for b in ('UpperArm', 'UpperArmTwist', 'Forearm', 'ForearmTwist')) > ARMW)[0] for s in 'LR'}
THIGHF = {s: [tuple(f.vertices) for f in body.data.polygons if all(DOM[i] in (f'B_{s}_Thigh',) for i in f.vertices)] for s in 'LR'}
PLATES = [o for o in bpy.data.objects if o.name in ('Arm_chest', 'Arm_belt') or o.name.startswith('Arm_spine_')]
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))


def ev(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = e.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(o.matrix_world.to_3x3()).T + np.array(o.matrix_world.translation)


def depth(trees, pts):
    worst = 0.0
    for t in trees:
        for p in pts:
            loc, nrm, _, d = t.find_nearest(Vector(p), REACH)
            if loc is not None and d > TOL and (Vector(p) - loc).dot(nrm) < -.5 * d: worst = max(worst, d)
    return worst


report = {}
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; n = int(act.frame_range[1])
    need = {s: np.zeros(n + 1) for s in 'LR'}; base = {s: 0.0 for s in 'LR'}
    for f in range(n + 1):
        sc.frame_set(f); B = ev(body)
        plate_trees = [BVHTree.FromPolygons(ev(o).tolist(), [tuple(p.vertices) for p in o.data.polygons]) for o in PLATES]
        fwd = (armik.W(rig, 'B_Spine2').to_3x3() @ CHEST_FWD).normalized()
        for s, sg in (('L', 1), ('R', -1)):
            o = 'R' if s == 'L' else 'L'
            trees = plate_trees + [BVHTree.FromPolygons(B.tolist(), THIGHF[o])]
            pts = np.vstack([B[ARMV[s]], ev(bpy.data.objects[f'Arm_forearm_{s}'])])
            sh = np.array(armik.W(rig, f'B_{s}_UpperArm').translation)
            d0 = depth(trees, pts); base[s] = max(base[s], d0)
            if d0 == 0: continue
            for deg in np.arange(STEP, MAXD + 1e-6, STEP):
                R = np.array(Matrix.Rotation(math.radians(sg * deg), 3, fwd))
                if depth(trees, (pts - sh) @ R.T + sh) == 0: need[s][f] = deg; break
            else:
                need[s][f] = MAXD
    r = 4; kern = np.exp(-.5 * (np.arange(-r, r + 1) / 1.5) ** 2); kern /= kern.sum(); keys = {}
    for s, sg in (('L', 1), ('R', -1)):
        sm = np.convolve(np.pad(need[s], r, mode='edge'), kern, mode='valid'); sm = np.maximum(sm, need[s]); need[s] = sm
    for f in range(n + 1):
        if need['L'][f] < .05 and need['R'][f] < .05: continue
        sc.frame_set(f); fwd = (armik.W(rig, 'B_Spine2').to_3x3() @ CHEST_FWD).normalized()
        for s, sg in (('L', 1), ('R', -1)):
            if need[s][f] < .05: continue
            M = armik.W(rig, f'B_{s}_UpperArm')
            armik.set_world(rig, f'B_{s}_UpperArm', armik.rot_world(M, Matrix.Rotation(math.radians(sg * need[s][f]), 3, fwd) @ M.to_3x3().normalized()))
        keys[f] = {s: rig.pose.bones[f'B_{s}_UpperArm'].rotation_quaternion.copy() for s in 'LR'}
    for f, kv in keys.items():
        for s, q in kv.items():
            pb = rig.pose.bones[f'B_{s}_UpperArm']; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    report[act.name] = {'worst_depth_before_cm': {s: round(base[s] * 100, 2) for s in 'LR'}, 'max_extra_abduction_deg': {s: round(float(need[s].max()), 1) for s in 'LR'},
                        'frames_turned': len(keys)}
    print('ARMCLEAR', act.name, json.dumps(report[act.name]), flush=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
(P / 'review/cand_armclear.json').write_text(json.dumps(report, indent=2) + '\n')
