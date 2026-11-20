"""Report UV islands and texel density (texels/cm at 2048) per region; island membership of the face front."""
import bpy, bmesh, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Peasant']; me = mesh.data
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
# islands: faces connected through edges that are not UV-split
key = lambda l: (round(l[uv].uv.x, 6), round(l[uv].uv.y, 6))
island = [-1] * len(bm.faces); n = 0
for f in bm.faces:
    if island[f.index] >= 0: continue
    stack = [f]; island[f.index] = n
    while stack:
        g = stack.pop()
        for l in g.loops:
            e = l.edge
            for o in e.link_faces:
                if o is g or island[o.index] >= 0: continue
                la = [x for x in o.loops if x.vert in e.verts]
                lb = [x for x in g.loops if x.vert in e.verts]
                ua = {x.vert.index: key(x) for x in la}; ub = {x.vert.index: key(x) for x in lb}
                if ua == ub:
                    island[o.index] = n; stack.append(o)
    n += 1
print('ISLANDS', n)
def uv_area(f):
    pts = [l[uv].uv for l in f.loops]
    return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
used = sum(uv_area(f) for f in bm.faces)
print('ATLAS_USED %.1f%%' % (used * 100))
def density(sel):
    a3 = sum(f.calc_area() for f in sel); a2 = sum(uv_area(f) for f in sel)
    return math.sqrt(a2 * 2048 ** 2 / a3) / 100 if a3 else 0
body = PARTS.index('Body')
face = [f for f in bm.faces if part[f.index] == body and f.calc_center_median().z > 1.38 and f.calc_center_median().y < -0.04]
hands = [f for f in bm.faces if part[f.index] == body and abs(f.calc_center_median().x) > 0.33]
print('DENSITY face %.1f hands %.1f' % (density(face), density(hands)))
for i, name in enumerate(PARTS):
    sel = [f for f in bm.faces if part[f.index] == i]
    print('DENSITY', name, '%.1f' % density(sel), 'islands', len({island[f.index] for f in sel}))
print('FOOT', '%.2f' % density([f for f in bm.faces if part[f.index] == body and f.calc_center_median().z < 0.1]))
print('FACE islands', sorted({island[f.index] for f in face}), 'sizes', [sum(1 for x in island if x == k) for k in sorted({island[f.index] for f in face})])
groups = {g.index: g.name for g in mesh.vertex_groups}
def reg(v):
    best, w = '', 0.0
    for g in v.groups:
        if g.weight > w: best, w = groups[g.group], g.weight
    return best.replace('mixamorig:', '')
vr = [reg(v) for v in me.vertices]
from collections import Counter
cnt = Counter()
regf = {}
for f in bm.faces:
    if part[f.index] != body: continue
    r = Counter(vr[v.index] for v in f.verts).most_common(1)[0][0]
    regf.setdefault(r, []).append(f)
for r, fs in sorted(regf.items(), key=lambda x: -len(x[1])):
    print('REGION', r, len(fs), '%.1f' % density(fs), 'islands', len({island[f.index] for f in fs}))
