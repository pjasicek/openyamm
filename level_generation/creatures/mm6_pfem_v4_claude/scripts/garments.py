"""Label every loose part of the natm body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin, 1 mantle (feather cape over the shoulders and back), 2 hip trim (feather cards around the belt), 3 leg guard
L, 4 leg guard R, 5 front panel + belt (P01), 6 back panel (P10), 7 arm ring, 8 bead/collar, 9 eye.
Cards are grouped by proximity (union of pieces with vertices within 8 mm of each other), then each group is named by
where it sits. Writes the 'garment' point attribute and work/garments.json; renders a coloured check.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
pieces = sorted(set(pv.tolist()))
kd = KDTree(nv)
for i, c in enumerate(co):
    kd.insert(c, i)
kd.balance()
par = {p: p for p in pieces}
def find(p):
    while par[p] != p:
        par[p] = par[par[p]]; p = par[p]
    return p
FIXED = {0: 0, 1: 5, 10: 6}
for p in pieces:                                   # rings, beads and eyes by shape before the proximity grouping
    m = pv == p; c = co[m].mean(0); lo, hi = co[m].min(0), co[m].max(0)
    if p in FIXED:
        continue
    if (hi - lo).max() < 0.035 and c[2] > 1.5:
        FIXED[p] = 9
    elif abs(c[0]) > 0.17 and 1.1 < c[2] < 1.35 and m.sum() > 18 and (hi - lo)[2] < 0.11 and (hi - lo)[0] > 0.1:
        FIXED[p] = 7                               # arm ring: wide in x and y, short in z
    elif c[1] < -0.15 and 1.2 < c[2] < 1.42 and (hi - lo).max() < 0.05:
        FIXED[p] = 8                               # tooth beads / small chest pieces
for i in range(nv):
    a = pv[i]
    if a in FIXED:
        continue
    for c, j, d in kd.find_range(co[i], 0.008):
        b = pv[j]
        if b != a and b not in FIXED:
            ra, rb = find(a), find(b)
            if ra != rb:
                par[ra] = rb
groups = {}
for p in pieces:
    if p not in FIXED:
        groups.setdefault(find(p), []).append(p)
lab = {p: g for p, g in FIXED.items() if g in (0, 5, 6, 7, 8, 9)}
rep = []
for r, ps in groups.items():
    m = np.isin(pv, ps); c = co[m].mean(0); lo, hi = co[m].min(0), co[m].max(0); n = int(m.sum())
    if len(ps) <= 2 and (hi - lo).max() < 0.035 and c[2] > 1.5:
        g = 9
    elif len(ps) <= 2 and hi[2] - lo[2] < 0.06 and abs(c[0]) > 0.12 and 1.0 < c[2] < 1.4:
        g = 7
    elif len(ps) <= 3 and c[1] < -0.1 and 1.15 < c[2] < 1.45:
        g = 8
    elif hi[2] < 0.65:
        g = 3 if c[0] > 0 else 4
    elif lo[2] > 0.75 and hi[2] < 1.12 and (len(ps) > 1 or c[1] < 0.06):
        g = 2
    else:
        g = 1
    for p in ps:
        lab[p] = g
    rep.append({'root': int(r), 'n_pieces': len(ps), 'verts': n, 'centre': [round(float(x), 3) for x in c],
                'lo': [round(float(x), 3) for x in lo], 'hi': [round(float(x), 3) for x in hi], 'garment': g})
for x in sorted(rep, key=lambda x: -x['verts']):
    print('GARMENTGROUP', json.dumps(x))
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(10)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
# check render: vertex colours by garment
cols = [(0.75, 0.6, 0.5), (0.3, 0.4, 0.95), (0.95, 0.75, 0.1), (0.2, 0.8, 0.3), (0.1, 0.6, 0.2), (0.9, 0.2, 0.2),
        (0.9, 0.3, 0.8), (0.1, 0.9, 0.9), (1, 1, 1), (0, 0, 0)]
ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'POINT')
for i in range(nv):
    ca.data[i].color = (*cols[gv[i]], 1)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
common.render_views(os.path.join(common.REVIEW, 'garments'), 0.85, 1.8, views=('front', 'left', 'back'), resolution=(500, 800), distance=20)
