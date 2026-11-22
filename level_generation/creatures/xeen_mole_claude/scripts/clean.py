"""Clean the Smart Topology mole (work/clean_v1.blend, pieces ranked by vertex count as prep.py lists them):
keep piece 0 (the closed body with head, snout and both clawed hands; its 9-edge hole filled), the eyeballs (4, 5)
and their front caps (15, 16), and the hind toe claws (6-13, decimated to 45 %). Dropped: piece 1 (a hidden inner
shell), the ~430 loose fur shingle plates (the fur is paint) and the two mirrored side tails (2, 3). Adds one centred
procedural tail (tapered tube on a Catmull-Rom centreline, rising behind the rump as in 02_back). Face attribute
`part`: 0 body, 1 eyes, 2 hind claws, 3 tail. Writes work/clean_v2.blend (object Mole)."""
import bpy, bmesh, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Mole']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
label = [-1] * len(bm.verts); pieces = []
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = len(pieces); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = label[v.index]; st.append(w)
    pieces.append(idx)
order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
rank = {p: r for r, p in enumerate(order)}
PART = {0: 0, 4: 1, 5: 1, 15: 1, 16: 1, **{k: 2 for k in range(6, 14)}}
vrank = [rank[label[v.index]] for v in bm.verts]
bmesh.ops.delete(bm, geom=[v for v in bm.verts if vrank[v.index] not in PART], context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
keep_rank = [r for r in vrank if r in PART]
part_layer = bm.faces.layers.int.new('part')
rank_layer = bm.verts.layers.int.new('rank')
for v, r in zip(bm.verts, keep_rank):
    v[rank_layer] = r
for f in bm.faces:
    f[part_layer] = PART[f.verts[0][rank_layer]]
# fill the body's hole(s)
bnd = [e for e in bm.edges if e.is_boundary and all(v[rank_layer] == 0 for v in e.verts)]
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
bmesh.ops.triangulate(bm, faces=res['faces'])
for f in res.get('faces', []):
    f[part_layer] = 0
print('FILLED body boundary edges', len(bnd), 'new faces', len(res['faces']))
# decimate the hind claws (dissolve-free: collapse via a temporary object after writing)
bm.to_mesh(ob.data); bm.free()
me = ob.data
# hind claws: decimate only part 2 faces using a vertex group + modifier
claw_vg = ob.vertex_groups.new(name='claws')
cl = set()
for p in me.polygons:
    if me.attributes['part'].data[p.index].value == 2:
        cl.update(p.vertices)
claw_vg.add(list(cl), 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
t0 = len(me.polygons)
d = ob.modifiers.new('d', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = 0.94
d.vertex_group = 'claws'; d.vertex_group_factor = 1.0; d.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d')
ob.vertex_groups.remove(ob.vertex_groups['claws'])
print('CLAW decimation', t0, '->', len(ob.data.polygons))
if 'rank' in me.attributes:
    me.attributes.remove(me.attributes['rank'])

# ---- tail: tapered tube on a Catmull-Rom centreline
P = [Vector(p) for p in ((0, 0.46, 0.24), (0, 0.58, 0.24), (0, 0.70, 0.27), (0, 0.80, 0.34), (0, 0.86, 0.44),
                         (0, 0.88, 0.54), (0, 0.865, 0.62))]


def cr(t):
    n = len(P) - 1; f = min(n - 1e-6, t * n); i = int(f); u = f - i
    p0 = P[max(0, i - 1)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(n, i + 2)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


SEG, RINGS = 8, 18
tb = bmesh.new()
rings = []
prev_n = Vector((1, 0, 0))
for k in range(RINGS + 1):
    t = k / RINGS
    c = cr(t); tan = (cr(min(1, t + 0.01)) - cr(max(0, t - 0.01))).normalized()
    side = Vector((1, 0, 0)); up = tan.cross(side).normalized(); side = up.cross(tan).normalized()
    r = 0.042 * (1 - t) + 0.011 * t
    rings.append([tb.verts.new(c + (side * math.cos(2 * math.pi * j / SEG) + up * math.sin(2 * math.pi * j / SEG)) * r)
                  for j in range(SEG)])
for k in range(RINGS):
    for j in range(SEG):
        a, b = rings[k][j], rings[k][(j + 1) % SEG]; c2, d2 = rings[k + 1][(j + 1) % SEG], rings[k + 1][j]
        tb.faces.new((a, b, c2, d2))
tipdir = (cr(1.0) - cr(0.97)).normalized()
tip = tb.verts.new(cr(1.0) + tipdir * 0.012)
for j in range(SEG):
    tb.faces.new((rings[-1][j], rings[-1][(j + 1) % SEG], tip))
root = tb.verts.new(cr(0.0) - (cr(0.03) - cr(0.0)).normalized() * 0.02)
for j in range(SEG):
    tb.faces.new((rings[0][(j + 1) % SEG], rings[0][j], root))
bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
bmesh.ops.triangulate(tb, faces=tb.faces, quad_method='SHORT_EDGE')
tme = bpy.data.meshes.new('Tail'); tb.to_mesh(tme)
tail = bpy.data.objects.new('Tail', tme); bpy.context.scene.collection.objects.link(tail)
pa = tme.attributes.new('part', 'INT', 'FACE')
for i in range(len(tme.polygons)):
    pa.data[i].value = 3
for o in bpy.data.objects: o.select_set(o in (ob, tail))
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
me = ob.data
for p in me.polygons:
    p.use_smooth = True
counts = {}
for p in me.polygons:
    v = me.attributes['part'].data[p.index].value; counts[v] = counts.get(v, 0) + 1
print('CLEAN tris', len(me.polygons), 'by part', dict(sorted(counts.items())))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
