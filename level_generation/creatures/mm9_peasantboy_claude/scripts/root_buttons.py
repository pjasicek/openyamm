"""Root the vest's small loose pieces (toggles, the collar toggle, the buckle: Meshy loose parts under MAXV vertices, not
head or hand faces) rigidly on the cloth behind them: every vertex of a piece takes the weights of the body vertex
nearest to the piece's centroid (not in the piece), so the piece rides with the cloth instead of floating 8 mm off it
in Death (detached_parts_audit.py); a piece floating 4-12 mm off the cloth at rest is set down 2 mm off it. Args: <in blend> <out blend> [maxv 60]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
MAXV = int(a[2]) if len(a) > 2 else 60
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int['head']; hn = bm.faces.layers.int.get('hand')
comp = [-1] * len(bm.verts); parts = []
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = len(parts); cur = [v.index]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = len(parts); st.append(y); cur.append(y.index)
    parts.append(cur)
headish = set()
for f in bm.faces:
    if f[hl] or (hn and f[hn]):
        headish.update(v.index for v in f.verts)
small = [p for p in parts if len(p) <= MAXV and not (set(p) & headish)]
inpart = set(i for p in small for i in p)
co = [v.co.copy() for v in bm.verts]
bm.free()
kd = KDTree(len(co))
for i, c in enumerate(co):
    if i not in inpart and i not in headish:
        kd.insert(c, i)
kd.balance()
rep = []
for p in small:
    c = sum((co[i] for i in p), Vector()) / len(p)
    _, j, d = kd.find(c)
    src = [(g.group, g.weight) for g in me.vertices[j].groups]
    for i in p:
        for g in list(me.vertices[i].groups):
            body.vertex_groups[g.group].remove([i])
        for gi, w in src:
            body.vertex_groups[gi].add([i], w, 'REPLACE')
    moved = 0.0
    if 0.004 < d < 0.012:                 # a toggle floating off the vest at rest (detached audit: 7.9 mm): set it down
        # on the cloth, 2 mm off it, along the line to the nearest cloth vertex
        mv = (co[j] - c) * ((d - 0.002) / d)
        for i in p:
            me.vertices[i].co += mv
        moved = round((d - 0.002) * 1000, 1)
    rep.append({'verts': len(p), 'centre': [round(x, 3) for x in c], 'from': j, 'dist_mm': round(d * 1000, 1), 'moved_mm': moved})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ROOTBUTTONS', rep)
