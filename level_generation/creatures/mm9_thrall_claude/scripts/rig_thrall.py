"""Step C: MM9 skeleton (true-handed), joints translated to the fit's J2 + pivots at the outside of the bend, rest rotations MM9's. Bone heat on the closed skin, then rules by part:
face and hair rigid over the neck band, sandals on the foot, ropes on the skin under them, skirt on eight hinges `Skirt_*`, children of Bip01 Spine.
Fingers come from graft_hands.py, helpers from helpers_thrall.py. Args: <graft blend> <mm9 glb> <joints npz> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
IN, MM9, JNPZ, OUT = sys.argv[sys.argv.index('--') + 1:]
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
J0 = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
Z = np.load(JNPZ); B = 'Bip01 '
J = dict(J0)
for k in Z.files:
    if B + k in J: J[B + k] = Z[k].copy()
PIV = {'L Calf': (0, 0.03, 0), 'R Calf': (0, 0.03, 0), 'L Forearm': (0, 0.015, 0), 'R Forearm': (0, 0.015, 0), 'L Thigh': (0, -0.025, 0), 'R Thigh': (0, -0.025, 0)}
for k, d in PIV.items(): J[B + k] = J[B + k] + np.array(d)
HR = 0.232  # hinge height above the Spine joint's level is taken from the skirt's top
me = body.data
n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
# hinges: eight round the skirt's top ring
sk = np.nonzero(pa == 1)[0]
ztop = P[sk, 2].max(); ring = sk[P[sk, 2] > ztop - 0.09]
cx, cy = 0.5 * (P[sk, 0].min() + P[sk, 0].max()), 0.5 * (P[ring, 1].min() + P[ring, 1].max())
HZ = ztop - 0.075
ANG = np.radians([-112.5, -67.5, -22.5, 22.5, 67.5, 112.5, 157.5, -157.5])
RING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SFL', 'Skirt_SBL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SBR', 'Skirt_SFR']
rx, ry = 0.5 * np.ptp(P[ring, 0]), 0.5 * np.ptp(P[ring, 1])
print('RIG skirt top', round(ztop, 3), 'hinge z', round(HZ, 3), 'centre', round(cx, 3), round(cy, 3), 'radii', round(rx, 3), round(ry, 3), 'skirt bottom', round(P[sk, 2].min(), 3))
HINGES = {nm: np.array([cx + rx * 0.9 * np.cos(a), cy + ry * 0.9 * np.sin(a), HZ]) for nm, a in zip(RING, ANG)}
# ---------- move the joints (translation only), add hinges
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.inverted()
for nm, q in J.items():
    e = eb[nm]; d = e.tail - e.head; e.head = Mi @ Vector(q); e.tail = e.head + d
sp = eb['Bip01 Spine']; Rt = sp.matrix.to_3x3()
for nm, h in HINGES.items():
    b = eb.new(nm); hp = Mi @ Vector(h)
    b.head = hp; b.tail = hp + Rt.col[1] * 0.08; b.align_roll(Rt.col[2]); b.parent = sp; b.use_connect = False; b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in rig.data.bones]; bid = {b: i for i, b in enumerate(bones)}
for nm, h in HINGES.items(): J[nm] = h
# ---------- temp segment rig + bone heat on the skin
SEG = []
def chain(names, tip=None):
    for a, b in zip(names[:-1], names[1:]): SEG.append((a, J[a], J[b]))
    if tip is not None: SEG.append((names[-1], J[names[-1]], tip))
chain([B + 'Spine', B + 'Spine2', B + 'Spine3', B + 'Neck', B + 'Head'], J[B + 'Head'] + np.array([0, -0.02, 0.2]))
for s in 'LR':
    SEG.append((B + f'{s} Clavicle', J[B + f'{s} Clavicle'], J[B + f'{s} UpperArm']))
    tip = J[B + f'{s} Hand'] + (J[B + f'{s} Finger1'] - J[B + f'{s} Hand']) * 1.8
    chain([B + f'{s} UpperArm', B + f'{s} Forearm', B + f'{s} Hand'], tip)
    toe = J[B + f'{s} Toe0'] + np.array([0.01, -0.08, 0.0])
    chain([B + f'{s} Thigh', B + f'{s} Calf', B + f'{s} Foot', B + f'{s} Toe0'], toe)
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
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] not in (0, 10)], context='VERTS')
oids = np.array([v[oid] for v in bm.verts])
bm.to_mesh(skin.data); bm.free()
for o in bpy.data.objects: o.select_set(False)
skin.select_set(True); hr.select_set(True); bpy.context.view_layer.objects.active = hr
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
W = np.zeros((n, len(bones)))
for v in skin.data.vertices:
    for g in v.groups:
        W[oids[v.index], bid[skin.vertex_groups[g.group].name]] = g.weight
tot = W.sum(1)
print('RIG heat: skin verts with no weight', int(((tot == 0) & np.isin(pa, (0, 10))).sum()), 'of', int(np.isin(pa, (0, 10)).sum()))
bpy.data.objects.remove(skin); bpy.data.objects.remove(hr)
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
def only(m, b): W[m] = 0; W[m, bid[B + b]] = 1
C = np.array([0.0, -0.205, 0.655]); Nk = np.array([0.0, -0.62, 0.785]); Nk /= np.linalg.norm(Nk); HF = 0.02
hh = (P - C) @ Nk - HF
# the arms stay: a stray vertex of the torso heat on the wrong side is a mirror issue: symmetric below
# head above the neck band
m = pa == 10
wh = sstep(hh, -0.02, 0.085)
W[m] = 0; W[m, bid[B + 'Head']] = wh[m]; W[m, bid[B + 'Neck']] = 1 - wh[m]
only(pa == 13, 'Head')
m = pa == 11; only(m, 'Head')
pt = sstep(P[:, 1], -0.19, -0.11) * (1 - sstep(P[:, 2], 0.72, 0.84)) * 0.75
W[m, bid[B + 'Ponytail1']] = pt[m]; W[m, bid[B + 'Head']] = 1 - pt[m]
# skirt: hinges round the ring, by height
q = np.nonzero(pa == 1)[0]
ang = np.arctan2(P[q, 1] - cy, P[q, 0] - cx)
r = sstep(HZ + 0.01 - P[q, 2], 0.0, 0.11)
A = np.sort(ANG); order = np.argsort(ANG)
aa = np.where(ang < A[0], ang + 2 * np.pi, ang)
A2 = np.r_[A, A[0] + 2 * np.pi]
sw = np.zeros((len(q), 8))
for k in range(8):
    mm = (aa >= A2[k]) & (aa < A2[k + 1])
    u = (aa[mm] - A2[k]) / (A2[k + 1] - A2[k]); u = u * u * (3 - 2 * u)
    sw[mm, k] = 1 - u; sw[mm, (k + 1) % 8] = u
W[q] = 0
for k in range(8):
    W[q, bid[RING[order[k]]]] = sw[:, k] * r
W[q, bid[B + 'Spine']] = 1 - r
# sandals: the foot skin under them
skn = np.nonzero(np.isin(pa, (0,)))[0]
kd = KDTree(len(skn))
for i in skn: kd.insert(P[i], int(i))
kd.balance()
for i in np.nonzero(pa == 5)[0]: W[i] = W[kd.find(P[i])[1]]
# belt and collar copy the skin; a tube must not shear, so they are smoothed along themselves
compids = np.unique(comp[np.isin(pa, (3, 6))])
big = {}
for c in compids:
    ids = np.nonzero(comp == c)[0]; ext = np.ptp(P[ids], 0)
    kind = 'collar' if pa[ids[0]] == 6 else ('belt' if ext[0] > 0.2 else 'loose')
    big[c] = (kind, ids)
    print('RIG rope part', kind, len(ids), np.round(P[ids].mean(0), 3).tolist())
for c, (kind, ids) in big.items():
    if kind in ('belt', 'collar'):
        for i in ids: W[i] = W[kd.find(P[i])[1]]
        for _ in range(40):
            W[ids] = np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in ids])
# rope ends and knots hang on the skirt under them: copy the nearest skirt vertex (the hem side rides its hinges), knots at the belt copy the belt
kds = KDTree(len(q))
for i in q: kds.insert(P[i], int(i))
kds.balance()
for c, (kind, ids) in big.items():
    if kind == 'loose':
        tgt = kds.find(P[ids].mean(0))[1]
        W[ids] = W[tgt]
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(bones)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
print('RIG zero weight verts', int((W.sum(1) < 0.5).sum()))
for b in bones: body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bid[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = rig; body.matrix_parent_inverse = rig.matrix_world.inverted()
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
fa = me.attributes.new('fpart', 'INT', 'FACE')
fv = [int(pa[p.vertices[0]]) for p in me.polygons]; fa.data.foreach_set('value', fv)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIGGED', n, len(bones))
