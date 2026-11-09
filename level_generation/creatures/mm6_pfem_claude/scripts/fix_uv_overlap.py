"""Resolve UV overlaps left by the conformal unwrap (closed rings fold onto themselves).

Overlapping triangle pairs are found by rasterising triangle ids at 1024^2. The copy on the hidden side
(back of the body, y > 0) is moved, with a one-ring margin, to a new planar-projected island in free atlas space
(face attribute uvfix = 1, refilled in compose). The visible partner is marked uvfix = 2 so compose inpaints
its texels from surrounding clean texels. Topology and existing UVs elsewhere are unchanged.
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

R = 1024
mesh = bpy.data.objects['Peasant']; me = mesh.data
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
me.calc_loop_triangles()
uvl = me.uv_layers.active.data
tris = list(me.loop_triangles)
owner = np.full((R, R), -1, dtype=np.int64)
pairs = set()
for ti, t in enumerate(tris):
    p = np.array([tuple(uvl[li].uv) for li in t.loops]) * R
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, R - 1), min(y1, R - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = p
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
    w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
    inside = (w0 > 0.02) & (w1 > 0.02) & (1 - w0 - w1 > 0.02)
    ys, xs = np.nonzero(inside)
    prev = owner[y0 + ys, x0 + xs]
    for q in np.unique(prev[prev >= 0]):
        if tris[q].polygon_index != t.polygon_index:
            pairs.add((int(q), ti))
    owner[y0 + ys, x0 + xs] = ti
centre = lambda ti: sum((me.vertices[v].co for v in tris[ti].vertices), Vector()) / 3
move_polys, mark_polys = set(), set()
for a, b in pairs:
    hidden, visible = (a, b) if centre(a).y > centre(b).y else (b, a)
    move_polys.add(tris[hidden].polygon_index); mark_polys.add(tris[visible].polygon_index)
print('OVERLAP pairs', len(pairs), 'move', len(move_polys), 'mark', len(mark_polys))
if os.environ.get('OVERLAP_REPORT'):
    import collections
    PARTS = json.loads(bpy.context.scene['pfem_parts'])
    part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
    groups = {g.index: g.name for g in mesh.vertex_groups}
    def label(ti):
        pi = tris[ti].polygon_index; pn = PARTS[part[pi]]
        if pn != 'Body': return pn
        v = me.vertices[tris[ti].vertices[0]]
        best = max(v.groups, key=lambda g: g.weight) if v.groups else None
        return 'Body:' + (groups[best.group].replace('mixamorig:', '') if best else '?')
    cnt = collections.Counter(tuple(sorted((label(a), label(b)))) for a, b in pairs)
    for k, n in cnt.most_common(25): print('PAIR', n, k)
    raise SystemExit
if not move_polys:
    raise SystemExit
# grow the moved set by one ring so the new island is a clean patch
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
grown = set(move_polys)
for fi in move_polys:
    for v in bm.faces[fi].verts:
        for f in v.link_faces:
            if f.index not in mark_polys:
                grown.add(f.index)
uv = bm.loops.layers.uv.active
faces = [bm.faces[i] for i in grown]
n = sum((f.normal * f.calc_area() for f in faces), Vector()).normalized()
u_ax = n.orthogonal().normalized(); v_ax = n.cross(u_ax).normalized()
pts = {l: Vector((l.vert.co.dot(u_ax), l.vert.co.dot(v_ax))) for f in faces for l in f.loops}
lo = Vector((min(p.x for p in pts.values()), min(p.y for p in pts.values())))
size = Vector((max(p.x for p in pts.values()), max(p.y for p in pts.values()))) - lo
scale = 29.0 * 100 / 2048            # head density, texels/cm -> UV units per metre
w, h = size.x * scale, size.y * scale
# free spot: coarse occupancy of all other faces
occ = np.zeros((128, 128), bool)
for f in bm.faces:
    if f.index in grown:
        continue
    us = [l[uv].uv for l in f.loops]
    x0, x1 = int(min(p.x for p in us) * 128), int(max(p.x for p in us) * 128)
    y0, y1 = int(min(p.y for p in us) * 128), int(max(p.y for p in us) * 128)
    occ[max(y0 - 1, 0):min(y1 + 2, 128), max(x0 - 1, 0):min(x1 + 2, 128)] = True
cw, ch = int(math.ceil(w * 128)) + 2, int(math.ceil(h * 128)) + 2
spot = None
for yy in range(0, 128 - ch):
    for xx in range(0, 128 - cw):
        if not occ[yy:yy + ch, xx:xx + cw].any():
            spot = ((xx + 1) / 128, (yy + 1) / 128); break
    if spot:
        break
if spot is None:
    raise RuntimeError('no free atlas space for the moved patch')
for l, p in pts.items():
    l[uv].uv = (spot[0] + (p.x - lo.x) * scale, spot[1] + (p.y - lo.y) * scale)
bm.to_mesh(me); bm.free()
if 'uvfix' in me.attributes:
    me.attributes.remove(me.attributes['uvfix'])
attr = me.attributes.new('uvfix', 'INT', 'FACE')
vals = [0] * len(me.polygons)
for i in mark_polys:
    vals[i] = 2
for i in grown:
    vals[i] = 1
attr.data.foreach_set('value', vals)
print('UVFIX moved', len(grown), 'polys to', spot, 'size', round(w, 4), round(h, 4), 'marked', len(mark_polys))
bpy.ops.wm.save_mainfile()
