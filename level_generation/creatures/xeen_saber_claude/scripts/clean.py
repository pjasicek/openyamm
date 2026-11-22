"""Clean the Smart Topology sabertooth (work/clean_v1.blend, pieces ranked by vertex count as prep.py lists them).

Meshy built a three-quarter body: the trunk's front half sits 6 cm to the right of its rear (shear) and the head is
yawed 19 degrees to the cat's left. The chest ruff is an overlapping open shell over the chest (an 85-edge boundary),
the cheek and both flanks have small holes, and the whiskers, lip rods and fur plates are 40 loose pieces.

Steps: straighten every vertex (x shear by the trunk midline per y; head yawed back by 19 degrees about a neck
pivot with a smooth falloff along the neck, then centred); keep piece 0 (body), the left eyeball (5), the left fang
(12) and the left paws' claw pieces (ranks 24-40 with x > 0); drop the rest. The body's tail is cut at y 0.47 and
every hole filled, then the body is voxel-remeshed (fuses the ruff shell and the lip slit into one closed surface),
smoothed lightly, cut at x = 0, its left half (the camera side of the master) mirrored, and reduced with a symmetric
collapse (the head keeps more triangles). The kept pieces are mirrored too. One procedural tail (tapered tube on a
Catmull-Rom centreline hanging from the rump and curling up at the tip, as in the masters) replaces Meshy's.
Face attribute `part`: 0 body, 1 eyes, 2 fangs, 3 claws, 4 tail. Writes work/voxel_body.npz (the mirrored voxel body) and
work/clean_parts.blend (Extras, Tail); reduce_voxel.py and clean_finish.py follow."""
import bpy, bmesh, os, math, sys
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOX = float(os.environ.get('VOX', '0.006'))
BODY_TRIS = int(os.environ.get('BODY_TRIS', '8000'))
YAW, HEAD_DX = -19.0, 0.03
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Saber']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()


def pieces_of(b):
    label = [-1] * len(b.verts); out = []
    for v in b.verts:
        if label[v.index] >= 0: continue
        st = [v]; label[v.index] = len(out); idx = []
        while st:
            x = st.pop(); idx.append(x.index)
            for e in x.link_edges:
                w = e.other_vert(x)
                if label[w.index] < 0: label[w.index] = label[v.index]; st.append(w)
        out.append(idx)
    return label, out


label, pieces = pieces_of(bm)
order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
rank = {p: r for r, p in enumerate(order)}
vrank = np.array([rank[label[v.index]] for v in bm.verts])


# ---- straighten
def midline(y):
    return np.interp(y, [-0.55, 0.05], [-0.095, -0.035])


co = np.array([v.co[:] for v in bm.verts])
co[:, 0] -= midline(co[:, 1])
t = np.clip((-0.70 - co[:, 1]) / (-0.70 + 0.92), 0, 1); w = t * t * (3 - 2 * t)
a = np.radians(YAW) * w; py = -0.80
x, y = co[:, 0].copy(), co[:, 1] - py
co[:, 0] = x * np.cos(a) - y * np.sin(a) + HEAD_DX * w
co[:, 1] = x * np.sin(a) + y * np.cos(a) + py
for v, c in zip(bm.verts, co):
    v.co = Vector(c)

# ---- keep / drop
cent = {r: co[vrank == r].mean(0) for r in set(vrank.tolist())}
KEEP = {0: 0, 5: 1, 12: 2}
for r in range(24, 41):
    if r in cent and cent[r][0] > 0.0 and cent[r][2] < 0.06:
        KEEP[r] = 3
print('KEEP', {r: KEEP[r] for r in sorted(KEEP)})
bmesh.ops.delete(bm, geom=[v for v in bm.verts if int(vrank[v.index]) not in KEEP], context='VERTS')
bm.verts.ensure_lookup_table()
rl = bm.verts.layers.int.new('rank')
kept_rank = [int(r) for r in vrank if int(r) in KEEP]
for v, r in zip(bm.verts, kept_rank):
    v[rl] = r


def split(b, sel, name):
    c = b.copy(); c.verts.ensure_lookup_table()
    lay = c.verts.layers.int['rank']
    bmesh.ops.delete(c, geom=[v for v in c.verts if not sel(v[lay])], context='VERTS')
    me = bpy.data.meshes.new(name); c.to_mesh(me); c.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


body = split(bm, lambda r: r == 0, 'Body')
extras = split(bm, lambda r: r != 0, 'Extras')
bpy.data.objects.remove(ob, do_unlink=True)

# ---- body: cut the tail, fill every hole
b = bmesh.new(); b.from_mesh(body.data)
bmesh.ops.delete(b, geom=[v for v in b.verts if v.co.y > 0.47], context='VERTS')
# close every boundary loop with a centroid fan (holes_fill left loops open, and one open loop makes the voxel
# remesh a thin double wall): the voxel step needs a watertight body
nfan = 0
while True:
    bnd = [e for e in b.edges if e.is_boundary]
    if not bnd:
        break
    e0 = bnd[0]; loop = [e0.verts[0], e0.verts[1]]; prev = e0
    while True:
        nxt = [e for e in loop[-1].link_edges if e.is_boundary and e is not prev]
        if not nxt: break
        prev = nxt[0]; w = prev.other_vert(loop[-1])
        if w is loop[0]: break
        loop.append(w)
    # orient the fan like the faces beside the loop: the loop runs along the neighbouring face in reverse
    f0 = e0.link_faces[0]; fv = list(f0.verts); i = fv.index(e0.verts[0])
    forward = fv[(i + 1) % len(fv)] is e0.verts[1]
    if forward: loop = loop[::-1]
    c = b.verts.new(sum((v.co for v in loop), Vector()) / len(loop))
    for k in range(len(loop)):
        b.faces.new((loop[k], loop[(k + 1) % len(loop)], c))
    nfan += 1
print('FILLED loops', nfan, 'boundary left', sum(1 for e in b.edges if e.is_boundary))
b.to_mesh(body.data); b.free()


def activate(o):
    for x in bpy.data.objects: x.select_set(x == o)
    bpy.context.view_layer.objects.active = o


activate(body)
body.data.remesh_voxel_size = VOX; body.data.remesh_voxel_adaptivity = 0.0
bpy.ops.object.voxel_remesh()
print('VOXEL faces', len(body.data.polygons))
sm = body.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 4
bpy.ops.object.modifier_apply(modifier='smooth')
# keep the voxel components but the largest (voxel bubbles)
b = bmesh.new(); b.from_mesh(body.data); b.verts.ensure_lookup_table()
lab2, pcs = pieces_of(b)
big = max(range(len(pcs)), key=lambda i: len(pcs[i]))
bmesh.ops.delete(b, geom=[v for v in b.verts if lab2[v.index] != big], context='VERTS')
print('VOXEL components', len(pcs))
# mirror the left half (x >= 0): the camera side of the three-quarter master
bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0),
                       clear_inner=True)
for v in b.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0.0
b.to_mesh(body.data); b.free()
mir = body.modifiers.new('mir', 'MIRROR'); mir.use_clip = True; mir.use_mirror_merge = True; mir.merge_threshold = 1e-4
bpy.ops.object.modifier_apply(modifier='mir')
tri = body.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier='tri')
# Blender's collapse stalls near 40k on this surface: scripts/reduce_voxel.py reduces it (MeshLab quadric)
activate(body)
vb = np.array([v.co[:] for v in body.data.vertices]); fb = np.array([p.vertices[:] for p in body.data.polygons])
np.savez(os.path.join(HERE, 'work', 'voxel_body.npz'), co=vb, tris=fb)
print('VOXEL_BODY tris', len(body.data.polygons))
# ---- extras: mirror the left eye, fang and claws
activate(extras)
claws_vg = extras.vertex_groups.new(name='claws')
lay = extras.data.attributes['rank']
cl = [v.index for v in extras.data.vertices if lay.data[v.index].value >= 24]
claws_vg.add(cl, 1.0, 'REPLACE')
d2 = extras.modifiers.new('d', 'DECIMATE'); d2.ratio = 1.0; d2.vertex_group = 'claws'; d2.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d')
if 'claws' in extras.vertex_groups: extras.vertex_groups.remove(extras.vertex_groups['claws'])
eb = bmesh.new(); eb.from_mesh(extras.data)
part_rank = eb.verts.layers.int['rank']
dup = bmesh.ops.duplicate(eb, geom=eb.verts[:] + eb.edges[:] + eb.faces[:])
for v in dup['geom']:
    if isinstance(v, bmesh.types.BMVert): v.co.x = -v.co.x
bmesh.ops.reverse_faces(eb, faces=[f for f in dup['geom'] if isinstance(f, bmesh.types.BMFace)])
pl = eb.faces.layers.int.new('part')
for f in eb.faces:
    f[pl] = KEEP[f.verts[0][part_rank]]
eb.to_mesh(extras.data); eb.free()

# ---- procedural tail
P = [Vector(p) for p in ((0, 0.40, 0.90), (0, 0.52, 0.91), (0, 0.66, 0.84), (0, 0.78, 0.68), (0, 0.86, 0.50),
                         (0, 0.93, 0.33), (0, 1.01, 0.22), (0, 1.11, 0.20), (0, 1.19, 0.26))]


def cr(t):
    n = len(P) - 1; f = min(n - 1e-6, t * n); i = int(f); u = f - i
    p0 = P[max(0, i - 1)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(n, i + 2)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


SEG, RINGS = 10, 26
tb = bmesh.new(); rings = []
for k in range(RINGS + 1):
    t = k / RINGS
    c = cr(t); tan = (cr(min(1, t + 0.01)) - cr(max(0, t - 0.01))).normalized()
    side = Vector((1, 0, 0)); up = tan.cross(side).normalized(); side = up.cross(tan).normalized()
    r = 0.062 * (1 - t) + 0.030 * t + 0.008 * math.exp(-((t - 0.93) / 0.05) ** 2)   # slight tuft near the tip
    rings.append([tb.verts.new(c + (side * math.cos(2 * math.pi * j / SEG) + up * math.sin(2 * math.pi * j / SEG)) * r)
                  for j in range(SEG)])
for k in range(RINGS):
    for j in range(SEG):
        tb.faces.new((rings[k][j], rings[k][(j + 1) % SEG], rings[k + 1][(j + 1) % SEG], rings[k + 1][j]))
tipdir = (cr(1.0) - cr(0.97)).normalized()
tip = tb.verts.new(cr(1.0) + tipdir * 0.025)
for j in range(SEG):
    tb.faces.new((rings[-1][j], rings[-1][(j + 1) % SEG], tip))
root = tb.verts.new(cr(0.0) - (cr(0.03) - cr(0.0)).normalized() * 0.03)
for j in range(SEG):
    tb.faces.new((rings[0][(j + 1) % SEG], rings[0][j], root))
bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
bmesh.ops.triangulate(tb, faces=tb.faces, quad_method='SHORT_EDGE')
tme = bpy.data.meshes.new('Tail'); tb.to_mesh(tme); tb.free()
tail = bpy.data.objects.new('Tail', tme); bpy.context.scene.collection.objects.link(tail)

a = tail.data.attributes.new('part', 'INT', 'FACE')
for i in range(len(tail.data.polygons)):
    a.data[i].value = 4
bpy.data.objects.remove(body, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_parts.blend'))
print('SAVED clean_parts.blend')
