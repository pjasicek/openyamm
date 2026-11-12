"""Fit the MM9 guard skeleton to the cleaned body (approved Yrsa route, limb fit of mm9_imp_claude/scripts/fit_imp.py): joints TRANSLATED,
rest rotations unchanged. Joint estimates E on the mesh (fit_guard.json, slices in work/clean_v1.npz: the MM9 knee sits 7 cm low on this
body); FK with MM9's bone directions and our lengths; the mesh posed there by a transient skin, so MM9's clips give MM9's poses.
Args: <clean blend> <config json> <out blend> <report json>  (MM6 guard copy: config fit_gua.json)"""
import bpy, sys, json
import numpy as np
from mathutils import Vector, Matrix
SRC, CFG, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG)); rep = {}
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
P = np.array([tuple(v.co) for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
nbr = [[] for _ in range(len(P))]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)


def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)


E = {}
for k, v in cfg['estimates'].items():
    E[k] = np.array(v, float)
    if ' R ' in k: E[k.replace(' R ', ' L ')] = np.array(v, float) * [-1, 1, 1]
newJ = {}
for k, v in cfg['centre'].items():
    newJ[k] = np.array(v, float)
T = {}; limbs = []
for S in 'RL':
    for bs, end_e, end_m in cfg['limbs']:
        limbs.append(([b.replace('{S}', S) for b in bs], end_e.replace('{S}', S), end_m.replace('{S}', S)))
for k, v in cfg.get('fixed', {}).items():
    for S in 'RL':
        newJ[k.replace('{S}', S)] = np.array(v, float) * ([1, 1, 1] if S == 'R' else [-1, 1, 1])
for bones, end_e, end_m in limbs:
    for k, b in enumerate(bones):
        if k == 0: newJ[b] = E[b].copy()
        if k + 1 < len(bones):
            c = bones[k + 1]
            R = rot_between(E[c] - E[b], J[c] - J[b])
            newJ[c] = newJ[b] + (J[c] - J[b]) / np.linalg.norm(J[c] - J[b]) * np.linalg.norm(E[c] - E[b])
        else:
            R = rot_between(E[end_e] - E[b], J[end_m] - J[b])
            newJ[end_m] = newJ[b] + (J[end_m] - J[b]) / np.linalg.norm(J[end_m] - J[b]) * np.linalg.norm(E[end_e] - E[b])
        T[b] = (R, E[b].copy(), newJ[b].copy())
rep['limb_rot_deg'] = {b: round(float(np.degrees(np.arccos(np.clip((np.trace(T[b][0]) - 1) / 2, -1, 1)))), 1) for b in T}
names = [b for l in limbs for b in l[0]]
seg = {}
for bones, end_e, end_m in limbs:
    for k, b in enumerate(bones):
        c = bones[k + 1] if k + 1 < len(bones) else None
        seg[b] = (E[b], E[c] if c else E[end_e])


def seg_d(Q, a, b):
    ab = b - a
    t = np.clip((Q - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(Q - a - np.outer(t, ab), axis=1)


D = np.stack([seg_d(P, *seg[b]) for b in names], 1)
side = np.array([np.sign(J[b][0]) for b in names])
D = np.where(np.sign(P[:, 0])[:, None] == side, D, 1e3)
best = D.argmin(1); dbest = D.min(1)
lab = np.zeros((len(P), len(names) + 1))
isleg = np.array([('Thigh' in names[b]) for b in best])
isarm = np.array([('UpperArm' in names[b]) for b in best])
free = (dbest < cfg['limb_radius']) & ~(isleg & (P[:, 2] > cfg['thigh_top_z'])) & ~(isarm & (np.abs(P[:, 0]) < cfg['arm_min_x']))
free &= ~np.isin(vp, [7, 9, 10])
lab[np.arange(len(P)), np.where(free, best + 1, 0)] = 1
for _ in range(cfg['blend_iters']):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
Q = lab[:, 0:1] * P
for i, b in enumerate(names):
    R, e, n_ = T[b]
    Q = Q + lab[:, i + 1:i + 2] * ((P - e) @ R.T + n_)
# loose pieces rigid with their centroid's label
comp = -np.ones(len(P), int); c_ = 0
for i in range(len(P)):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
for c in range(c_):
    ids = np.nonzero(comp == c)[0]
    if len(ids) > 700 or vp[ids[0]] in (1, 2, 3, 5, 7, 9): continue
    w = lab[ids].mean(0)
    Mx = w[0] * np.eye(4)
    for i, b in enumerate(names):
        R, e, n_ = T[b]
        M = np.eye(4); M[:3, :3] = R; M[:3, 3] = n_ - R @ e
        Mx = Mx + w[i + 1] * M
    Q[ids] = P[ids] @ Mx[:3, :3].T + Mx[:3, 3]
P = Q
rep['floor_after'] = float(P[:, 2].min()); rep['x_max'] = float(np.abs(P[:, 0]).max())
for v, p in zip(me.vertices, P): v.co = Vector(p)
for name in J:
    if name in newJ: continue
    p = parent[name]
    while p is not None and p not in newJ: p = parent[p]
    newJ[name] = J[name] + ((newJ[p] - J[p]) if p else np.zeros(3))
rep['joint_moves_cm'] = {n: round(float(np.linalg.norm(newJ[n] - J[n]) * 100), 1) for n in J}
json.dump({n: newJ[n].tolist() for n in J}, open(OUT + '.joints.json', 'w'), indent=0)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
Mi = arm.matrix_world.inverted()
for eb in arm.data.edit_bones:
    d = Mi.to_3x3() @ Vector(newJ[eb.name] - J[eb.name])
    eb.head += d; eb.tail += d
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps({k: v for k, v in rep.items() if k != 'joint_moves_cm'})[:900])
