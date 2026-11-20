"""MM7 Sea Monster (shark) rig, quadruped playbook (own rig, automatic weights), forward -Y, up +Z, left +X.
Joints from the mesh: the centreline is the per-slab median (x, z) of the vertices between snout (y min) and tail tip
(y max); fins are a small share of each slab's vertices, so the median stays in the body. Bone points are fixed
fractions of the length from the snout (FRAC). Bones:
  Spine1 (root, mid-body, points forward) - Spine2 (chest) - Head (to the snout tip) - Jaw (lower jaw, hinge -> chin)
  Tail1..6 (parent Spine1, mid-body -> tail fin tip; Tail6 carries the caudal fin)
  Fin_L / Fin_R (pectoral fins, root -> tip, parent Spine2)
Weights: Blender automatic (heat) weights on the closed shell (work/joints.json lists any proxy setting); the lower
jaw is then set by geometry: vertices in front of the hinge and below the mouth line (work/joints.json 'mouth')
follow Jaw, feathered over 1.5 cm across the line; teeth/gum pieces follow the jaw half they sit in.
Writes work/joints.json (if missing: measured) and work/rig_v1.blend. Args: none"""
import bpy, bmesh, os, sys, math, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
y0, y1 = co[:, 1].min(), co[:, 1].max(); L = y1 - y0
PV = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PV); SKIN = PV == 0
JP = os.path.join(HERE, 'work', 'joints.json')
J = json.load(open(JP)) if os.path.exists(JP) else {}
FRAC = J.get('frac', {'Head': [0.20, 0.0], 'Spine2': [0.33, 0.20], 'Spine1': [0.45, 0.33],
                      'Tail': [0.45, 0.55, 0.64, 0.72, 0.79, 0.86, 1.0]})


def centre(f):
    y = y0 + f * L; w = 0.02 * L
    sel = np.abs(co[:, 1] - y) < w
    while sel.sum() < 12:
        w *= 1.5; sel = np.abs(co[:, 1] - y) < w
    c = co[sel & SKIN][:, [0, 2]] if (sel & SKIN).sum() >= 12 else co[sel][:, [0, 2]]
    m = c.mean(0)
    for _ in range(4):                                  # trimmed centroid: the fins fall out
        d = np.linalg.norm(c - m, axis=1); m = c[d <= np.percentile(d, 60)].mean(0)
    return Vector((float(m[0]), float(y), float(m[1])))


def at(f):
    p = centre(f)
    if f <= 0.001:                                                       # the snout tip itself
        i = int(np.argmin(co[:, 1])); p = Vector(co[i])
    if f >= 0.999:
        i = int(np.argmax(co[:, 1])); p = Vector(co[i])
    return p


ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones


def bone(name, h, t, parent=None, connect=False, up=Vector((0, 0, 1))):
    b = eb.new(name); b.head = h; b.tail = t; b.align_roll(up); b.parent = eb[parent] if parent else None
    b.use_connect = connect
    return b


s1 = bone('Spine1', at(FRAC['Spine1'][0]), at(FRAC['Spine1'][1]))
bone('Spine2', at(FRAC['Spine2'][0]), at(FRAC['Spine2'][1]), 'Spine1', True)
bone('Head', at(FRAC['Head'][0]), at(FRAC['Head'][1]), 'Spine2', True)
tp = [at(f) for f in FRAC['Tail']]
for i in range(len(tp) - 1):
    bone(f'Tail{i + 1}', tp[i], tp[i + 1], 'Spine1' if i == 0 else f'Tail{i}', i > 0)
M = J.get('mouth')
if M:
    bone('Jaw', Vector(M['hinge']), Vector(M['chin']), 'Head')
for s, sg in (('L', 1.0), ('R', -1.0)):
    F = J.get('fins', {}).get(s)
    if F:
        bone(f'Fin_{s}', Vector(F['root']), Vector(F['tip']), 'Spine2', up=Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in ad.bones]
print('RIG bones', names)
# ---------------------------------------------------------------- automatic weights
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
gi = {g.name: g.index for g in body.vertex_groups}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        if body.vertex_groups[e.group].name in names:
            W[v.index, names.index(body.vertex_groups[e.group].name)] = e.weight
print('RIG heat: unweighted', int((W.sum(1) < 1e-6).sum()))
# ---------------------------------------------------------------- jaw by geometry
if M:
    # the mouth line: z_line(y) interpolated between the hinge (y_h, z_h) and the snout corner (y_s, z_s)
    yh, zh, ys, zs = M['line'][0][0], M['line'][0][1], M['line'][1][0], M['line'][1][1]
    zl = zh + (co[:, 1] - yh) * (zs - zh) / (ys - yh)
    infront = co[:, 1] < yh + 0.01
    d = zl - co[:, 2]                                           # > 0 below the line
    w = np.clip(0.5 + d / 0.03, 0, 1) * np.clip((yh + 0.01 - co[:, 1]) / 0.03, 0, 1) * infront
    j = names.index('Jaw'); hd = names.index('Head')
    move = w > 0
    W[move] *= (1 - w[move])[:, None]; W[move, j] += w[move]
    # teeth (pieces 1-36): each wholly on Head or Jaw by its centre against the lip line
    for p in range(1, PV.max() + 1):
        idx = np.where(PV == p)[0]
        if not len(idx):
            continue
        W[idx] = 0; W[idx, j if co[idx, 2].mean() < M['teeth_split_z'] else hd] = 1.0
    print('RIG jaw vertices', int((w > 0.5).sum()), 'teeth on the jaw', sum(1 for p in range(1, PV.max() + 1) if (PV == p).any() and co[PV == p, 2].mean() < M['teeth_split_z']))
good = np.where(W.sum(1) > 0.5)[0]; lost = np.where(W.sum(1) <= 0.5)[0]
if len(lost):                                           # heat-solver misses: the nearest weighted vertex's weights
    kd = KDTree(len(good))
    for i, g in enumerate(good):
        kd.insert(co[g], i)
    kd.balance()
    for i in lost:
        W[i] = W[good[kd.find(co[i])[1]]]
print('RIG filled', len(lost), 'unweighted vertices from their nearest weighted neighbour')
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
top = np.argsort(-W, 1)[:, :4]; W2 = np.zeros_like(W); rows = np.arange(nv)[:, None]
W2[rows, top] = W[rows, top]; W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for jx, n in enumerate(names):
    g = body.vertex_groups.new(name=n)
    for i in np.nonzero(W2[:, jx] > 1e-4)[0]:
        g.add([int(i)], float(W2[i, jx]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
print('RIG saved work/rig_v1.blend')
