"""(giant, from mm9_bigfoot_claude/rig_bf.py) Step C: MM9 skeleton (true-handed), joints translated to the fit (rest rotations MM9's). Bone heat on the closed skin, then rules: head rigid over the neck band, toes on Toe0, eyes on Head.
Args: <wrap blend> <mm9 glb> <joints npz> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
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
PIV = json.load(open(os.path.join(os.path.dirname(os.path.abspath(IN)), '..', 'scripts', 'pivots.json')))
for k, d in PIV.items(): J[B + k] = J[B + k] + np.array(d)
me = body.data
n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.inverted()
for nm, q in J.items():
    e = eb[nm]; d = e.tail - e.head; e.head = Mi @ Vector(q); e.tail = e.head + d
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in rig.data.bones]; bid = {b: i for i, b in enumerate(bones)}
SEG = []
def chain(names, tip=None):
    for a, b in zip(names[:-1], names[1:]): SEG.append((a, J[a], J[b]))
    if tip is not None: SEG.append((names[-1], J[names[-1]], tip))
chain([B + 'Pelvis', B + 'Spine', B + 'Spine2', B + 'Spine3', B + 'Neck', B + 'Head'], J[B + 'Head'] + np.array([0, -0.01, 0.25]))
for s in 'LR':
    SEG.append((B + f'{s} Clavicle', J[B + f'{s} Clavicle'], J[B + f'{s} UpperArm']))
    chain([B + f'{s} UpperArm', B + f'{s} Forearm', B + f'{s} Hand'], J[B + f'{s} Finger1'] + (J[B + f'{s} Finger1'] - J[B + f'{s} Hand']) * 0.5)
    chain([B + f'{s} Thigh', B + f'{s} Calf', B + f'{s} Foot', B + f'{s} Toe0'], J[B + f'{s} Toe0'] + np.array([0, -0.12, 0.02]))
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
print('RIG heat: skin verts with no weight', int(((W.sum(1) == 0) & (pa == 0)).sum()), 'of', int((pa == 0).sum()))
bpy.data.objects.remove(skin); bpy.data.objects.remove(hr)
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
fh = np.zeros(n, int); me.attributes['fromhead'].data.foreach_get('value', fh)
X, Y, Zz = P[:, 0], P[:, 1], P[:, 2]
inhead = np.abs(X) < 0.25
wh = sstep(Zz, 0.95, 0.99) * inhead                                                   # skull, face, hair above the jaw
wh = np.maximum(wh, fh * sstep(Zz, 0.89, 0.93) * sstep(np.abs(X), 0.085, 0.11) * inhead)   # side locks of hair
wh = np.maximum(wh, fh * (Y > 0.0) * sstep(Zz, 0.89, 0.96) * inhead)                       # hair mass behind the neck
wh = np.maximum(wh, fh * (Y < -0.13) * sstep(Zz, 0.915, 0.94) * inhead)                     # chin and beard
sk = pa == 0
hv = sk & (wh > 0)
W[hv] = W[hv] * (1 - wh[hv, None])
W[hv, bid[B + 'Head']] += wh[hv]
print('RIG head band', int(hv.sum()))
# feet: below the ankle rigid on Foot, toes on Toe0
for s in 'LR':
    f = J[B + f'{s} Foot']; g = J[B + f'{s} Toe0']
    m = sk & (np.sign(P[:, 0]) == (1 if s == 'L' else -1)) & (P[:, 2] < f[2] + 0.1) & (np.abs(P[:, 0]) < 0.5)
    t = 1 - sstep(P[:, 2], f[2] - 0.04, f[2] + 0.08)
    W[m] = W[m] * (1 - t[m, None]); W[m, bid[B + f'{s} Foot']] += t[m]
    t2 = sstep(-P[:, 1], -g[1] - 0.05, -g[1] + 0.03)
    W[m] = W[m] * (1 - t2[m, None]); W[m, bid[B + f'{s} Toe0']] += t2[m]
W[~sk] = 0; W[~sk, bid[B + 'Head']] = 1
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(bones)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
print('RIG zero weight verts', int((W.sum(1) < 0.5).sum()))
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
fv = [int(pa[p.vertices[0]]) for p in me.polygons]; fa.data.foreach_set('value', fv)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIGGED', n, len(bones))
