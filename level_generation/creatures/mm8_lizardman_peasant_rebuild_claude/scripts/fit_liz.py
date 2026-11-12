"""Fit the MM9 LIZARDORC skeleton to the Meshy lizardman body (after mm6_gua_rebuild_claude/scripts/fit_gua.py, the Yrsa
route's limb fit): joints TRANSLATED, rest rotations unchanged. Joint estimates E on our mesh (scripts/fit_liz.json:
Meshy auto-rig joints + centre chain read from grid views); each limb bone is laid along MM9's bone direction with our
segment length (FK), and the mesh is posed there by a transient skin (limb labels by distance to our segments, blended
over the mesh), so the MM9 clips' local rotations give MM9's poses on our proportions. Feet: MM9 has no toe joint; its
foot direction is the Foot bone's own weighted MM9 foot vertices' centroid.
Body: work/placed.npz (scripts/estimate.py placement). Args: <mm9 glb> <config> <out blend> <report json>"""
import bpy, sys, json, os
import numpy as np
from mathutils import Vector
MM9, CFG, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(CFG)); rep = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
mm9 = max(meshes, key=lambda o: len(o.data.vertices))
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
# MM9 foot direction: centroid of MM9 vertices whose strongest group is the foot
Mw = np.array(mm9.matrix_world); mco = np.array([tuple(v.co) for v in mm9.data.vertices]) @ Mw[:3, :3].T + Mw[:3, 3]
gn = {g.index: g.name for g in mm9.vertex_groups}
mlab = [gn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mm9.data.vertices]
for S in 'LR':
    sel = np.array([l == f'Bip01 {S} Foot' for l in mlab])
    J[f'FootEnd{S}'] = mco[sel].mean(0) if sel.any() else J[f'Bip01 {S} Foot'] + np.array([0, -0.1, -0.05])
    rep[f'mm9_foot_dir_{S}'] = (J[f'FootEnd{S}'] - J[f'Bip01 {S} Foot']).round(3).tolist()
for o in meshes: bpy.data.objects.remove(o, do_unlink=True)
D = np.load(os.path.join(HERE, 'work/placed.npz')); P = D['co'].astype(float); TRI = D['tri']
me = bpy.data.meshes.new('Body'); me.from_pydata(P.tolist(), [], TRI.tolist()); me.update()
body = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(body)
nbr = [[] for _ in range(len(P))]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)


def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)


E = {k: np.array(v, float) for k, v in cfg['estimates'].items()}
for S in 'LR':                                   # hand tip: centroid of the hand beyond the wrist
    h, f = E[f'Bip01 {S} Hand'], E[f'Bip01 {S} Forearm']; ax = (h - f) / np.linalg.norm(h - f)
    sel = (((P - h) @ ax) > 0.01) & (np.linalg.norm(P - h, axis=1) < 0.25) & (np.sign(P[:, 0] - cfg['centre']['Bip01 Pelvis'][0]) == (1 if S == 'L' else -1))
    E[f'Tip{S}'] = P[sel].mean(0)
    rep[f'tip_{S}'] = E[f'Tip{S}'].round(3).tolist()
newJ = {k: np.array(v, float) for k, v in cfg['centre'].items()}
T = {}; limbs = []
for S in 'RL':
    for bs, end_e, end_m in cfg['limbs']:
        limbs.append(([b.replace('{S}', S) for b in bs], end_e.replace('{S}', S), end_m.replace('{S}', S)))
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
    ab = b - a; t = np.clip((Q - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(Q - a - np.outer(t, ab), axis=1)


cx = cfg['centre']['Bip01 Pelvis'][0]
D_ = np.stack([seg_d(P, *seg[b]) for b in names], 1)
side = np.array([1 if ' L ' in b else -1 for b in names])
D_ = np.where(np.sign(P[:, 0] - cx)[:, None] == side, D_, 1e3)
best = D_.argmin(1); dbest = D_.min(1)
isleg = np.array([('Thigh' in names[b]) for b in best]); isarm = np.array([('UpperArm' in names[b]) for b in best])
free = (dbest < cfg['limb_radius']) & ~(isleg & (P[:, 2] > cfg['thigh_top_z'])) & ~(isarm & (np.abs(P[:, 0] - cx) < cfg['arm_min_x']))
lab = np.zeros((len(P), len(names) + 1)); lab[np.arange(len(P)), np.where(free, best + 1, 0)] = 1
for _ in range(cfg['blend_iters']):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
Q = lab[:, 0:1] * P
for i, b in enumerate(names):
    R, e, n_ = T[b]; Q = Q + lab[:, i + 1:i + 2] * ((P - e) @ R.T + n_)
P2 = Q
rep['floor_before'] = float(P[:, 2].min()); rep['floor_after'] = float(P2[:, 2].min())
for v, p in zip(me.vertices, P2): v.co = Vector(p)
for name in [b.name for b in arm.data.bones]:
    if name in newJ: continue
    p = parent[name]
    while p is not None and p not in newJ: p = parent[p]
    newJ[name] = J[name] + ((newJ[p] - J[p]) if p else np.zeros(3))
rep['joint_moves_cm'] = {n: round(float(np.linalg.norm(newJ[n] - J[n]) * 100), 1) for n in newJ if n in parent}
json.dump({n: newJ[n].tolist() for n in newJ}, open(OUT + '.joints.json', 'w'), indent=0)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
Mi = arm.matrix_world.inverted()
for eb in arm.data.edit_bones:
    d = Mi.to_3x3() @ Vector(newJ[eb.name] - J[eb.name]); eb.head += d; eb.tail += d
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = arm; body.matrix_parent_inverse = arm.matrix_world.inverted()
np.savez(OUT + '.posed.npz', co=P2, tri=TRI)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps({k: v for k, v in rep.items() if k != 'joint_moves_cm'})[:1500])
