"""Blade clearance for the candidate attacks (after cand_fit.py, before the cloth). The crescents are rigid on Blade_<S>
(child of the hand), so per frame and hand: the family and the larger Vreth crescent, posed, against the posed body
(without either hand's grip faces), the head, the other crescent and the floor. Where anything crosses, the hand turns
about the wrist by the smallest rotation (axes: forearm roll and the two wrist bends; 5..MAXDEG deg) that clears both
crescents and keeps the wrist swing <= WRIST_LIM; the rotation vectors are Gaussian-smoothed over time (never below a
frame's own need) and the pass repeats on what remains. Twist helpers are re-derived from the new hand.
Checked and keyed every STEPF frame (half frames: the set's whips pass a blade through a thigh between two frames).
With CLOTH=1 (a second run after cand_finish.py) the simulated skirt strips and mantle are obstacles too: a hem
reaching past its chain's last point is out of the simulation's blade capsules (Vreth's crescent tip through his
mantle on one frame); the few-degree turn there barely changes what the cloth reacts to. Report:
review/cand_blade_clear[_cloth].json.
Args: -- <in blend> <out blend>   (env MAXDEG 35, WRIST_LIM 60, PASSES 3, STEPF 0.5, CLOTH 0)"""
from pathlib import Path
import sys, os, json, math
import bpy, numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts')); import armik
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
MAXDEG, WRIST_LIM, PASSES = float(os.environ.get('MAXDEG', '35')), float(os.environ.get('WRIST_LIM', '60')), int(os.environ.get('PASSES', '3'))
STEPF = float(os.environ.get('STEPF', '0.5')); CLOTH = os.environ.get('CLOTH', '0') == '1'
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
GI = {g.index: g.name for g in body.vertex_groups}
DOM = [GI[max(v.groups, key=lambda x: x.weight).group] if v.groups else '' for v in body.data.vertices]
BF = [tuple(f.vertices) for f in body.data.polygons]
KEEP = [f for f in BF if not any('Hand' in DOM[i] or 'Finger' in DOM[i] for i in f)]
BL = {}
for s in 'LR':
    BL[s] = []
    for kind in ('Family', 'Vreth'):
        o = bpy.data.objects[f'{kind}_Blade_{s}']; inv = rig.data.bones[f'Blade_{s}'].matrix_local.inverted()
        BL[s].append((np.array([list(inv @ v.co) for v in o.data.vertices]), [tuple(p.vertices) for p in o.data.polygons]))


CLOTHO = [o for o in bpy.data.objects if CLOTH and o.type == 'MESH' and o.name.startswith(('Cloth_', 'Mantle_'))]


def world(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(o.matrix_world.to_3x3()).T + np.array(o.matrix_world.translation)


def body_tree():
    co = [world(body)]; faces = list(KEEP); off = len(co[0])
    for o in CLOTHO:
        V = world(o); faces += [tuple(off + i for i in p.vertices) for p in o.data.polygons]; co.append(V); off += len(V)
    return BVHTree.FromPolygons(np.vstack(co).tolist(), faces)


def blade_world(s, R=None, w=None):
    M = np.array(rig.matrix_world @ rig.pose.bones[f'Blade_{s}'].matrix); outv = []
    for V, F in BL[s]:
        X = V @ M[:3, :3].T + M[:3, 3]
        if R is not None: X = (X - w) @ R.T + w
        outv.append((X, F))
    return outv


def cost(blades, tree, others):
    c = 0
    for (X, F), (Xo, Fo) in zip(blades, others):
        t = BVHTree.FromPolygons(X.tolist(), F)
        c += len(t.overlap(tree)) + len(t.overlap(BVHTree.FromPolygons(Xo.tolist(), Fo))) + int((X[:, 2] < 0).sum())
    return c


def helpers():
    for sd in 'LR':
        fb = rig.data.bones[f'B_{sd}_Forearm']; hb = rig.data.bones[f'B_{sd}_Hand']
        axis = (fb.matrix_local.inverted() @ hb.head_local).normalized()
        rel = (rig.pose.bones[fb.name].matrix.inverted() @ rig.pose.bones[hb.name].matrix).to_quaternion()
        rest = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
        _, tw = armik.split_swing_twist(rel @ rest.inverted(), axis)
        pb = rig.pose.bones[f'B_{sd}_ForearmTwist']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(axis, .6 * tw)
    bpy.context.view_layer.update()


report = {}
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; n = int(act.frame_range[1])
    TS = np.arange(0, n + 1e-6, STEPF); m_ = len(TS)
    total = {s: np.zeros((m_, 3)) for s in 'LR'}; first = None; last = None
    for it in range(PASSES):
        need = {s: np.zeros((m_, 3)) for s in 'LR'}; left = 0
        for j, f in enumerate(TS):
            sc.frame_set(int(f), subframe=float(f - int(f))); tree = body_tree()
            for s in 'LR':
                o = 'R' if s == 'L' else 'L'; cur = blade_world(s); oth = blade_world(o); c0 = cost(cur, tree, oth)
                if c0 == 0: continue
                Mh = armik.W(rig, f'B_{s}_Hand'); w = np.array(Mh.translation)
                fa = (Mh.translation - armik.W(rig, f'B_{s}_Forearm').translation).normalized()
                e1 = fa.orthogonal().normalized(); e2 = fa.cross(e1)
                best = (c0, 0.0, None)
                for deg in np.arange(5, MAXDEG + 1e-6, 5):
                    for ax in (fa, -fa, e1, -e1, e2, -e2, (e1 + e2).normalized(), -(e1 + e2).normalized(), (e1 - e2).normalized(), -(e1 - e2).normalized()):
                        R = Matrix.Rotation(math.radians(deg), 3, ax)
                        sw, _ = armik.wrist_cost(rig, s, R @ Mh.to_3x3().normalized())
                        if sw > WRIST_LIM: continue
                        cc = cost(blade_world(s, np.array(R), w), tree, oth)
                        if cc < best[0]: best = (cc, deg, ax)
                    if best[0] == 0: break
                if best[2] is not None: need[s][j] = np.array(best[2]) * math.radians(best[1])
                left += best[0]
        if first is None: first = int(sum(np.linalg.norm(need[s], axis=1).astype(bool).sum() for s in 'LR'))
        last = left
        if not any(np.abs(need[s]).sum() for s in 'LR'): break
        r = int(4 / STEPF); kern = np.exp(-.5 * (np.arange(-r, r + 1) * STEPF / 1.5) ** 2); kern /= kern.sum()
        keys = {}
        for s in 'LR':
            sm = np.stack([np.convolve(np.pad(need[s][:, j], r, mode='edge'), kern, mode='valid') for j in range(3)], 1)
            mag, smag = np.linalg.norm(need[s], axis=1), np.linalg.norm(sm, axis=1)
            sm = np.where((mag > smag)[:, None], need[s], sm); total[s] += sm
            for j, f in enumerate(TS):
                v = sm[j]; a_ = float(np.linalg.norm(v))
                if a_ < 1e-5: continue
                sc.frame_set(int(f), subframe=float(f - int(f))); M = armik.W(rig, f'B_{s}_Hand')
                armik.set_world(rig, f'B_{s}_Hand', armik.rot_world(M, Matrix.Rotation(a_, 3, Vector(v / a_)) @ M.to_3x3().normalized()))
                keys.setdefault(f, {})[s] = rig.pose.bones[f'B_{s}_Hand'].rotation_quaternion.copy()
        for f, kv in keys.items():
            sc.frame_set(int(f), subframe=float(f - int(f)))
            for s, q in kv.items():
                pb = rig.pose.bones[f'B_{s}_Hand']; pb.rotation_quaternion = q
            bpy.context.view_layer.update(); helpers()
            for s in kv:
                rig.pose.bones[f'B_{s}_Hand'].keyframe_insert('rotation_quaternion', frame=float(f))
            for s in 'LR':
                rig.pose.bones[f'B_{s}_ForearmTwist'].keyframe_insert('rotation_quaternion', frame=float(f))
        print('CLEAR', act.name, 'pass', it, 'frames corrected', sum(len(v) for v in keys.values()), 'crossings left', left, flush=True)
    report[act.name] = {'frames_needing_turn_first_pass': first, 'max_turn_deg': {s: round(math.degrees(float(np.linalg.norm(total[s], axis=1).max())), 1) for s in 'LR'},
                        'crossings_left_last_check': last}
    print('CLEARED', act.name, json.dumps(report[act.name]), flush=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
(P / f"review/cand_blade_clear{'_cloth' if CLOTH else ''}.json").write_text(json.dumps(report, indent=2) + '\n')
