"""Step C: MM9 Yanmir skeleton (true-handed) on our A-posed body. MM9's bind is a stride with the right arm bent round the staff, so,
as mm9_highwayman_claude/fit_hw.py: joints move onto our mesh (limbs: cross-section centroids near estimates from the Meshy views;
spine, neck, head, clavicles: MM9's heights, centred in our torso), and each limb bone keeps MM9's frame turned by the least
rotation onto our limb (feet by yaw only, so soles stay level where MM9's are). The clips copy MM9's local rotations, so every bone
takes MM9's world rotation exactly and our mesh follows. Fingers, the staff bones and Ponytail1 follow their parent's turn.
Then bone heat on the skin (rig_bf.py), and rules: head rigid above the neck band, the beard on Ponytail1 (MM9 weights its beard
there), eyes on Head, feet rigid below the ankle, toes on Toe0.
Args: <wrap blend> <mm9 true glb> <out blend>   Writes <out>.joints.json, <out>.delta.json, <out>.report.json"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
IN, MM9, OUT = sys.argv[sys.argv.index('--') + 1:]
B = 'Bip01 '
# Meshy-view estimates (Meshy normalised: x, y, z) of the left arm, mapped as fit_yan.py (x, y * SC; z above the hip -0.08 + (z + 0.1) * SC)
SC = 2.55
EST_N = {'UpperArm': (0.155, 0.040, 0.215), 'Forearm': (0.207, 0.030, 0.045), 'Hand': (0.237, -0.025, -0.070), 'Tip': (0.243, -0.060, -0.165)}
EST = {k: np.array((v[0] * SC, v[1] * SC, -0.08 + (v[2] + 0.10) * SC)) for k, v in EST_N.items()}

bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=MM9)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.name = 'MM9_Rig'
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o not in (body, rig): bpy.data.objects.remove(o)
bpy.context.view_layer.update()
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
me = body.data; n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
sk = pa == 0
rep = {}


def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)


def section(p, axis, r, half=0.012, side=0):
    """centroid of skin vertices in a slab across axis at p within radius r (side: +1/-1 keeps that x side only)"""
    a = axis / np.linalg.norm(axis); d = P - p; t = d @ a; rad = np.linalg.norm(d - np.outer(t, a), axis=1)
    m = sk & (np.abs(t) < half) & (rad < r)
    if side: m &= np.sign(P[:, 0]) == side
    if m.sum() < 8: return p.copy(), 0
    q = P[m]; c = (q.min(0) + q.max(0)) / 2      # box centre: a slab's vertex mean leans to the denser side
    return c, int(m.sum())


newJ = {}
# centre chain: MM9 heights, centred front-to-back in our torso / neck
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2'):
    m = sk & (np.abs(P[:, 2] - J[B + k][2]) < 0.012) & (np.abs(P[:, 0]) < 0.10)
    y = (P[m, 1].min() + P[m, 1].max()) / 2 if m.sum() > 8 else J[B + k][1]
    newJ[B + k] = np.array((0.0, y, J[B + k][2]))
# neck and head: the hair and beard close round the neck in the wrap, so the slice cannot find it. Measured on the placed head
# model (work/face.npz, x = 0): throat skin y -0.06..-0.025, nape +0.03..+0.08 at z 0.90-0.92, so the neck's centre is y 0.0
newJ[B + 'Neck'] = np.array((0.0, 0.0, J[B + 'Neck'][2]))
newJ[B + 'Head'] = newJ[B + 'Neck'] + (J[B + 'Head'] - J[B + 'Neck'])
# beard: in front of the throat (y < -0.09) from the chin (z 0.98) down to its tip (0.86); Ponytail1 under the chin, inside it
newJ[B + 'Ponytail1'] = np.array((0.0, -0.105, 0.965))
D = {}
for S, sg in (('L', 1), ('R', -1)):
    M = np.array([sg, 1, 1]); X = lambda k: B + f'{S} ' + k
    newJ[X('Clavicle')] = J[B + 'L Clavicle'] * M
    newJ[X('Clavicle')][1] = newJ[B + 'Spine2'][1] + 0.5 * (newJ[B + 'Neck'][1] - newJ[B + 'Spine2'][1])
    e = {k: v * M for k, v in EST.items()}
    up = e['UpperArm'].copy()
    el, c1 = section(e['Forearm'], e['Hand'] - e['UpperArm'], 0.09, side=sg)
    wr, c2 = section(e['Hand'], e['Hand'] - e['Forearm'], 0.07, side=sg)
    rep[f'arm_{S}_section_counts'] = [c1, c2]
    tip = e['Tip']
    # legs: MM9 heights; hip x from MM9, knee and ankle as cross-section centres
    th = J[B + 'L Thigh'] * M
    kn, c3 = section(J[B + 'L Calf'] * M, np.array((0, 0, 1.0)), 0.13, side=sg)
    an, c4 = section(J[B + 'L Foot'] * M, np.array((0, 0, 1.0)), 0.13, side=sg)
    mt = sk & (np.sign(P[:, 0]) == sg) & (np.abs(P[:, 2] - th[2]) < 0.012) & (np.abs(P[:, 0] - th[0]) < 0.08)
    th[1] = (P[mt, 1].min() + P[mt, 1].max()) / 2 if mt.sum() > 8 else th[1]
    rep[f'leg_{S}_section_counts'] = [c3, c4]
    mf = sk & (np.sign(P[:, 0]) == sg) & (P[:, 2] < an[2] - 0.05) & (np.abs(P[:, 0] - an[0]) < 0.14)
    toe_y, heel_y = P[mf, 1].min(), P[mf, 1].max()
    toe = np.array((an[0] + (J[B + 'L Toe0'][0] - J[B + 'L Foot'][0]) * sg, heel_y + 0.68 * (toe_y - heel_y), J[B + 'L Toe0'][2]))
    rep[f'foot_{S}'] = {'heel_y': round(float(heel_y), 3), 'toe_y': round(float(toe_y), 3)}
    for k, v in (('UpperArm', up), ('Forearm', el), ('Hand', wr), ('Thigh', th), ('Calf', kn), ('Foot', an), ('Toe0', toe)):
        newJ[X(k)] = v
    D[X('Clavicle')] = rot_between(J[X('UpperArm')] - J[X('Clavicle')], newJ[X('UpperArm')] - newJ[X('Clavicle')])
    for a, b in (('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot')):
        D[X(a)] = rot_between(J[X(b)] - J[X(a)], newJ[X(b)] - newJ[X(a)])
    D[X('Hand')] = rot_between(J[X('Finger1')] - J[X('Hand')], tip - wr)
    a0 = J[X('Toe0')] - J[X('Foot')]; a1 = toe - an
    ang = np.arctan2(a1[1], a1[0]) - np.arctan2(a0[1], a0[0]); c, s_ = np.cos(ang), np.sin(ang)
    D[X('Foot')] = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    D[X('Toe0')] = D[X('Foot')]; D[X('Toe01')] = D[X('Foot')]
    newJ[X('Toe01')] = newJ[X('Toe0')] + D[X('Foot')] @ (J[X('Toe01')] - J[X('Toe0')])
    hand_scale = np.linalg.norm(tip - wr) / np.linalg.norm(J[X('Finger12')] - J[X('Hand')]) if False else 1.0
    for f in ('Finger0', 'Finger01', 'Finger1', 'Finger11', 'Finger12'):
        D[X(f)] = D[X('Hand')]
        newJ[X(f)] = newJ[X('Hand')] + D[X('Hand')] @ (J[X(f)] - J[X('Hand')])
    if S == 'R':
        for w in ('Ystaff', 'Ystafftop', 'Ystaffbot'):
            D[w] = D[X('Hand')]; newJ[w] = newJ[X('Hand')] + D[X('Hand')] @ (J[w] - J[X('Hand')])
rep['rest_turn_deg'] = {b: round(float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))), 1) for b, R in D.items()}
for k in J:
    if k not in newJ: newJ[k] = J[k].copy()
rep['joint_moves_cm'] = {k: round(float(np.linalg.norm(newJ[k] - J[k]) * 100), 1) for k in J}
rep['joints'] = {k: np.round(v, 3).tolist() for k, v in newJ.items() if ' R ' not in k}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mw = np.array(rig.matrix_world); Mi = np.linalg.inv(Mw)
for eb in rig.data.edit_bones:
    nm = eb.name
    Mb = Mw @ np.array(eb.matrix)
    R = D.get(nm, np.eye(3)) @ Mb[:3, :3]
    Mn = np.eye(4); Mn[:3, :3] = R; Mn[:3, 3] = newJ[nm]
    L = eb.length
    eb.matrix = Matrix((Mi @ Mn).tolist()); eb.length = L
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
rep['joint_error_mm'] = round(max(float(np.linalg.norm(np.array(tuple(rig.matrix_world @ rig.data.bones[k].head_local)) - newJ[k])) for k in newJ) * 1000, 3)
J = newJ
# ---- weights (rig_bf.py): bone heat on the skin over chains, then rules
bones = [b.name for b in rig.data.bones]; bid = {b: i for i, b in enumerate(bones)}
SEG = []


def chain(names, tip=None):
    for a, b in zip(names[:-1], names[1:]): SEG.append((a, J[a], J[b]))
    if tip is not None: SEG.append((names[-1], J[names[-1]], tip))


chain([B + 'Pelvis', B + 'Spine', B + 'Spine1', B + 'Spine2', B + 'Neck', B + 'Head'], J[B + 'Head'] + np.array([0, 0.0, 0.30]))
for s in 'LR':
    SEG.append((B + f'{s} Clavicle', J[B + f'{s} Clavicle'], J[B + f'{s} UpperArm']))
    chain([B + f'{s} UpperArm', B + f'{s} Forearm', B + f'{s} Hand'], J[B + f'{s} Hand'] + (J[B + f'{s} Hand'] - J[B + f'{s} Forearm']) * 0.55)
    chain([B + f'{s} Thigh', B + f'{s} Calf', B + f'{s} Foot', B + f'{s} Toe0'], J[B + f'{s} Toe0'] + np.array([0, -0.12, 0.0]))
ad = bpy.data.armatures.new('heat'); hr = bpy.data.objects.new('heat', ad); bpy.context.scene.collection.objects.link(hr)
bpy.context.view_layer.objects.active = hr
for o in bpy.data.objects: o.select_set(o is hr)
bpy.ops.object.mode_set(mode='EDIT')
for nm, a, b in SEG:
    e = ad.edit_bones.new(nm); e.head = Vector(a); e.tail = Vector(b)
bpy.ops.object.mode_set(mode='OBJECT')
skin = body.copy(); skin.data = me.copy(); skin.name = 'skin'; bpy.context.scene.collection.objects.link(skin)
bm = bmesh.new(); bm.from_mesh(skin.data); lay = bm.verts.layers.int['part']; oid = bm.verts.layers.int.new('oid')
bm.verts.ensure_lookup_table()
for v in bm.verts: v[oid] = v.index
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != 0], context='VERTS')
oids = np.array([v[oid] for v in bm.verts])
bm.to_mesh(skin.data); bm.free()
for o in bpy.data.objects: o.select_set(False)
skin.select_set(True); hr.select_set(True); bpy.context.view_layer.objects.active = hr
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
W = np.zeros((n, len(bones)))
for v in skin.data.vertices:
    for g in v.groups:
        W[oids[v.index], bid[skin.vertex_groups[g.group].name]] = g.weight
rep['heat_unweighted'] = int(((W.sum(1) == 0) & sk).sum())
bpy.data.objects.remove(skin); bpy.data.objects.remove(hr)


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def put(mask, w, bone):
    W[mask] = W[mask] * (1 - w[mask, None]); W[mask, bid[bone]] += w[mask]


# head rigid above the neck: a plane through the neck joint tilted so the hair at the back and the beard in front count as head
Nk = np.array([0.0, -0.25, 0.97]); Nk /= np.linalg.norm(Nk)
C = J[B + 'Neck'] + np.array([0.0, 0.0, 0.035])
hh = (P - C) @ Nk
wh = sstep(hh, -0.015, 0.05) * (1 - sstep(np.abs(P[:, 0]), 0.17, 0.24))
put(sk & (wh > 0), wh, B + 'Head')
# beard below the chin on Ponytail1 (MM9: Ponytail1 holds its beard tip)
pt = J[B + 'Ponytail1']
wb = sstep(0.975 - P[:, 2], 0.0, 0.05) * sstep(-0.075 - P[:, 1], 0.0, 0.025) * (1 - sstep(np.abs(P[:, 0]), 0.075, 0.105))
put(sk & (wb > 0) & (P[:, 2] > 0.80), wb, B + 'Ponytail1')
rep['beard_verts'] = int((sk & (wb > 0.5)).sum())
for s in 'LR':
    f = J[B + f'{s} Foot']; g = J[B + f'{s} Toe0']
    m = sk & (np.sign(P[:, 0]) == (1 if s == 'L' else -1)) & (P[:, 2] < f[2] + 0.1) & (np.abs(P[:, 0]) < 0.5)
    t = 1 - sstep(P[:, 2], f[2] - 0.04, f[2] + 0.06)
    put(m, t, B + f'{s} Foot')
    t2 = sstep(-P[:, 1], -g[1] - 0.04, -g[1] + 0.03)
    put(m, t2, B + f'{s} Toe0')
W[~sk] = 0; W[~sk, bid[B + 'Head']] = 1
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(bones)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
rep['zero_weight'] = int((W.sum(1) < 0.5).sum())
for b in bones: body.vertex_groups.new(name=b)
for j, b in enumerate(bones):
    ids = np.nonzero(W[:, j])[0]
    g = body.vertex_groups[b]
    for i in ids: g.add([int(i)], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bid[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = rig; body.matrix_parent_inverse = rig.matrix_world.inverted()
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
fa = me.attributes.new('fpart', 'INT', 'FACE')
fa.data.foreach_set('value', [int(pa[p.vertices[0]]) for p in me.polygons])
json.dump({k: v.tolist() for k, v in J.items()}, open(OUT + '.joints.json', 'w'), indent=0)
json.dump({k: v.tolist() for k, v in D.items()}, open(OUT + '.delta.json', 'w'), indent=0)
json.dump(rep, open(OUT + '.report.json', 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIG ' + json.dumps({k: v for k, v in rep.items() if k in ('rest_turn_deg', 'heat_unweighted', 'zero_weight', 'beard_verts', 'joint_error_mm')})[:1500])
print('RIGGED', n, len(bones))
