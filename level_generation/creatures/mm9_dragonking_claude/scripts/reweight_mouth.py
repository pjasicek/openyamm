"""Clean jaw split for the dragon head (after mm9_lobber_claude/scripts/reweight_head.py).

Args: <in blend> <out blend> <report json>

rig_dragon.py's diffusion smeared the upper/lower jaw labels across the lips, so opening the MM9 jaw (Rattack3,
rAttack1, WingAttack) dragged the lips into a stretched green bucket. Here the mouth line is the plane through the
MM9 jaw hinge (Xjawpivot) that best separates the MM9 head's upper-jaw vertices from its lower-jaw vertices
(z = a (y - y_hinge) + z_hinge, x-symmetric; grid search, fewest misclassified). Every Body vertex of the snout
(in front of the hinge, head- or jaw-weighted) is re-weighted rigidly: below the plane -> the jaw's own bone mix
(nearest MM9 lower vertex label: Xjaw / Xjawpivot / Xtong / chin fins), above -> the skull (nearest MM9 upper label),
with a linear blend over BAND around the plane only behind the snout (mouth corners, where cheek skin stretches).
Faces that then span the plane (vertices on both sides) are tagged 'lip' (face attribute) for the mouth texture.
"""
import bpy, sys, json, bmesh
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
BAND = 0.12
CORNER = 0.8   # blend only within CORNER of the hinge (along -y); the front of the mouth splits hard
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01', 'Xtong', 'Xtongpiv'}
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
hinge = Vector(arm.data.bones['Xjawpivot'].head_local)
mp, ml = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.endswith('.mesh') or o.name.startswith('MM9Posed'):
        continue
    for v in o.data.vertices:
        n = o.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name
        if n in UPPER or n in LOWER:
            mp.append(o.matrix_world @ v.co); ml.append(n)
MP = np.array([tuple(p) for p in mp]); ML = np.array(ml)
low = np.isin(ML, list(LOWER))
snout = MP[:, 1] < hinge.y
best = None
for a in np.linspace(-1.5, 1.5, 121):
    for b in np.linspace(-0.6, 0.6, 61):
        zp = a * (MP[:, 1] - hinge.y) + hinge.z + b
        below = MP[:, 2] < zp
        err = int(((below != low) & snout).sum())
        if best is None or err < best[0]:
            best = (err, a, b)
err, A_, B_ = best
kU = KDTree(int((~low).sum())); kL = KDTree(int(low.sum()))
iu = np.nonzero(~low)[0]; il = np.nonzero(low)[0]
for j, i in enumerate(iu):
    kU.insert(Vector(MP[i]), j)
for j, i in enumerate(il):
    kL.insert(Vector(MP[i]), j)
kU.balance(); kL.balance()
me = body.data
gi = {g.name: g.index for g in body.vertex_groups}
for n in UPPER | LOWER:
    if n not in gi:
        body.vertex_groups.new(name=n)
gi = {g.name: g.index for g in body.vertex_groups}
vgname = {g.index: g.name for g in body.vertex_groups}
side = np.zeros(len(me.vertices), np.int8)   # 0 untouched, 1 upper, -1 lower
changed = 0
for v in me.vertices:
    hw = sum(g.weight for g in v.groups if vgname[g.group] in UPPER | LOWER)
    if hw < 0.5 or v.co.y > hinge.y + 0.15:
        continue
    zp = A_ * (v.co.y - hinge.y) + hinge.z + B_
    d = v.co.z - zp
    t = 1.0 if d > 0 else 0.0
    if (hinge.y - v.co.y) < CORNER:
        t = float(np.clip(0.5 + d / (2 * BAND), 0, 1))
    side[v.index] = 1 if d > 0 else -1
    nu = ML[iu[kU.find(v.co)[1]]]
    nl = ML[il[kL.find(v.co)[1]]]
    rest = [(g.group, g.weight) for g in v.groups if vgname[g.group] not in UPPER | LOWER]
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([v.index])
    for gidx, w in rest:
        body.vertex_groups[gidx].add([v.index], w, 'REPLACE')
    if t > 0:
        body.vertex_groups[gi[nu]].add([v.index], hw * t, 'ADD')
    if t < 1:
        body.vertex_groups[gi[nl]].add([v.index], hw * (1 - t), 'ADD')
    changed += 1
lip = me.attributes.get('lip') or me.attributes.new('lip', 'BOOLEAN', 'FACE')
nlip = 0
for p in me.polygons:
    s = {int(side[i]) for i in p.vertices}
    flag = 1 in s and -1 in s
    lip.data[p.index].value = flag
    nlip += flag
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
rep = {'plane': {'a': round(float(A_), 3), 'b': round(float(B_), 3), 'misclassified_mm9': err,
                 'mm9_snout_vertices': int(snout.sum())}, 'reweighted': changed, 'lip_faces': nlip}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('MOUTH ' + json.dumps(rep))
