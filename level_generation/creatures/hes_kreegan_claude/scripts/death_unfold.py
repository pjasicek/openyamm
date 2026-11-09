"""hkr armour pass: the death's crouch folded the belly up into the v2 cuirass (chest plate 6 cm into the pelvis skin
at Death 1.0 s). Per frame of the clip: depth = the deepest cuirass vertex (Arm_* on B_Spine2 / B_Spine1 / B_Spine)
inside the skin of the pelvis, thighs and lower spine, or that skin inside a cuirass plate (closed-shell tests as
armour_gate.py); where it exceeds LIM,
the spine bones' (B_Spine, B_Spine1, B_Spine2) own rotations are eased toward rest by the smallest share (steps of
0.08, at most MAXK) that brings it under LIM, the shares smoothed over time (Gaussian, never below the need) and keyed;
the neck and head keep their world rotation (the look is unchanged). Run before death_floor.py (the floor pass
follows). Args: -- <in blend> <out blend> <Action>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
src, out, name = a[0], a[1], a[2]
LIM, MAXK, SIG = float(os.environ.get('LIM', '0.008')), float(os.environ.get('MAXK', '0.8')), 2.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene; AW = rig.matrix_world
me = body.data
GI = {g.index: g.name for g in body.vertex_groups}
DOM = [GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
LOW = {'B_Pelvis', 'B_Spine', 'B_L_Thigh', 'B_R_Thigh', 'B_Groin'}
ALLF = [tuple(f.vertices) for f in me.polygons]
LOWF = np.array([sum(DOM[k] in LOW for k in f) * 2 > len(f) for f in ALLF])
CUI = [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in ('B_Spine2', 'B_Spine1', 'B_Spine')]
LOWV = np.array([i for i, d in enumerate(DOM) if d in LOW], int)
PF = {o.name: [tuple(p.vertices) for p in o.data.polygons] for o in CUI}
# inner surfaces (make_armour's dark strip at the atlas corner): skin beyond them within 3 cm, over the plate (gate rule)
IF = {o.name: [tuple(p.vertices) for p in o.data.polygons if p.material_index == 0 and
               all(o.data.uv_layers[0].data[li].uv[0] > 0.99 for li in p.loop_indices)] for o in CUI}
SPINE = ['B_Spine', 'B_Spine1', 'B_Spine2']; KEEP = ['B_Neck', 'B_Head']
DIRS = [Vector((0.0123, 0.0217, 1.0)).normalized(), Vector((0.71, -0.33, -0.62)).normalized(), Vector((-0.55, 0.81, 0.2)).normalized()]


def parity(tree, p, maxd=1.2):
    votes = 0
    for d in DIRS:
        o = Vector(p); n = 0; tr = 0.0
        while tr < maxd:
            loc, nrm, fi, dist = tree.ray_cast(o, d, maxd - tr)
            if loc is None: break
            n += 1; tr += dist + 1e-5; o = loc + d * 1e-5
        votes += n % 2
    return votes >= 2


def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


def depth():
    bpy.context.view_layer.update()
    B = ev(body); full = BVHTree.FromPolygons(B.tolist(), ALLF); best = 0.0
    for o in CUI:
        P = ev(o); t = BVHTree.FromPolygons(P.tolist(), PF[o.name]); lo, hi = P.min(0) - 0.01, P.max(0) + 0.01
        for p in B[LOWV[np.all((B[LOWV] > lo) & (B[LOWV] < hi), axis=1)]]:   # belly skin through the plate
            loc, n, fi, d = t.find_nearest(Vector(p), 0.04)
            if loc is not None and d > best and (Vector(p) - loc).dot(n) < 0 and parity(t, p, 0.5): best = d
        ti = BVHTree.FromPolygons(P.tolist(), IF[o.name])
        for p in B[LOWV[np.all((B[LOWV] > lo) & (B[LOWV] < hi), axis=1)]]:
            loc, n, fi, d = ti.find_nearest(Vector(p), 0.03)
            if loc is not None and d > best:
                v = Vector(p) - loc
                if v.dot(n) < -0.9 * v.length: best = d
        for p in P:
            loc, n, fi, d = full.find_nearest(Vector(p), 0.08)
            if loc is None or d <= best or not LOWF[fi]: continue
            if (Vector(p) - loc).dot(n) < 0 and parity(full, p): best = d
    return best


def ease(k, base):
    """spine rotations eased toward rest by share k (from the frame's own keys in base); neck/head world kept"""
    keep = {n: (AW @ rig.pose.bones[n].matrix).to_3x3().normalized() for n in KEEP}
    for n in SPINE:
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion().slerp(base[n], 1 - k)
    bpy.context.view_layer.update()
    for n in KEEP:
        pb = rig.pose.bones[n]; M = AW @ pb.matrix
        R = keep[n].to_4x4(); R.translation = M.translation
        pb.matrix = AW.inverted() @ R; bpy.context.view_layer.update()


act = bpy.data.actions[name]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
need, before = [], []
for f in fr:
    sc.frame_set(f); d0 = depth(); before.append(d0); kk = 0.0
    if d0 > LIM:
        base = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in SPINE}
        kk = MAXK
        for c in np.arange(0.08, MAXK + 1e-6, 0.08):
            ease(float(c), base); dd = depth(); sc.frame_set(f)
            if dd <= LIM:
                kk = float(c); break
    need.append(kk)
need = np.array(need)
g = np.exp(-0.5 * (np.arange(-6, 7) / SIG) ** 2); g /= g.sum()
ks = np.maximum(np.convolve(np.pad(need, 6, mode='edge'), g, mode='valid'), need)
keys = {}
for f, k in zip(fr, ks):
    if k <= 0.01: continue
    sc.frame_set(f); base = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in SPINE}
    ease(float(k), base)
    keys[f] = {n: (rig.pose.bones[n].rotation_quaternion.copy() if n in SPINE else rig.pose.bones[n].matrix_basis.to_quaternion())
               for n in SPINE + KEEP}
prev = {}
for f in fr:
    if f not in keys: continue
    for n, q in keys[f].items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        if n in prev and q.dot(prev[n]) < 0: q = -q
        prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
after = []
for f in fr:
    sc.frame_set(f); after.append(depth())
rep = {'before_cm': round(max(before) * 100, 2), 'after_cm': round(max(after) * 100, 2),
       'ease_max': round(float(ks.max()), 2), 'frames': int((ks > 0.01).sum())}
print('DEATHUNFOLD', name, json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
