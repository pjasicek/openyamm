"""Soften the face's midline (positions only; UVs, weights and paints stay valid). The Meshy head was mirrored about
x = 0 (sym_meshy.py: the far arm and a thigh were broken), which left a crease down the forehead, a knife-edged nose
ridge with a spiked underside and a V-shaped chin. Head-shell vertices (`head` faces of the largest head part) in the
face box get WEIGHTED Laplacian steps: weight = falloff over |x| (1 at the midline, 0 at BAND) x the box's soft edges;
midline vertices stay at x = 0; the eye cups (|x| 0.012..0.038, z 0.725..0.76) are left alone. The result is made
exactly symmetric again. Only the largest head part (the face shell), below ZTOP. Args: <in blend> <out blend> [iters 6] [band 0.022] [ztop 0.73] [snap 0]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ITERS = int(a[2]) if len(a) > 2 else 6
BAND = float(a[3]) if len(a) > 3 else 0.022
ZTOP = float(a[4]) if len(a) > 4 else 0.73        # below the brows: the forehead keeps Meshy's shape (2026-11-02: a
                                                    # forehead step pulled a hair-painted fold into view)
SNAP = (a[5] if len(a) > 5 else '0') == '1'
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int['head']
hn = bm.faces.layers.int.get('hand')
headv = set()
for f in bm.faces:
    if f[hl] and not (hn and f[hn]):
        headv.update(v.index for v in f.verts)
# the face shell only (the largest connected head part): the lip plates and eyes are separate parts
comp = {}
for s0 in headv:
    if s0 in comp:
        continue
    st = [s0]; comp[s0] = s0; cur = [s0]
    while st:
        x = bm.verts[st.pop()]
        for e in x.link_edges:
            y = e.other_vert(x).index
            if y in headv and y not in comp:
                comp[y] = s0; st.append(y); cur.append(y)
from collections import Counter
big = Counter(comp.values()).most_common(1)[0][0]
headv = {i for i in headv if comp[i] == big}


def boxw(p):
    if p.y > -0.035:            # front of the face only
        return 0.0
    def ramp(x, a, b):
        return float(np.clip((x - a) / (b - a), 0, 1))
    wz = ramp(p.z, 0.598, 0.615) * (1 - ramp(p.z, ZTOP - 0.012, ZTOP))
    wx = max(0.0, 1 - abs(p.x) / BAND)
    eye = 0.012 < abs(p.x) < 0.038 and 0.722 < p.z < 0.762
    return 0.0 if eye else wz * wx


W = {i: boxw(bm.verts[i].co) for i in headv}
W = {i: w for i, w in W.items() if w > 0}
moved = 0
for it in range(ITERS):
    new = {}
    for i, w in W.items():
        v = bm.verts[i]
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v).index in headv]
        if len(nb) < 3:
            continue
        avg = sum((n.co for n in nb), Vector()) / len(nb)
        p = v.co.lerp(avg, 0.5 * w)
        if abs(v.co.x) < 1e-6:
            p.x = 0.0
        new[i] = p
    for i, p in new.items():
        bm.verts[i].co = p
    moved = len(new)
# exact symmetry from the +x side (optional: the snap can pick a vertex of another fold)
from mathutils.kdtree import KDTree
pos = [v for v in bm.verts if v.index in W and v.co.x > 1e-6]
kd = KDTree(len(pos))
for k, v in enumerate(pos):
    kd.insert(Vector((v.co.x, v.co.y, v.co.z)), k)
kd.balance()
worst = 0
for i in (W if SNAP else ()):
    v = bm.verts[i]
    if v.co.x < -1e-6:
        q, k, d = kd.find(Vector((-v.co.x, v.co.y, v.co.z)))
        if d < 0.004:
            v.co = Vector((-q.x, q.y, q.z)); worst = max(worst, d)
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FACESMOOTH', {'verts': len(W), 'moved': moved, 'iters': ITERS, 'band': BAND, 'sym_worst': round(worst, 5)})
