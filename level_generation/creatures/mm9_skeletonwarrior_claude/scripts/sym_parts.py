"""Clean the Meshy parts (all in the HD master's pose, on the MM9 scale):
- the human-looking face and jaw (parts 4, 2) go; the skull-only Smart Topology (cranium, separate mandible, separate teeth)
  is placed inside the helmet: chin at the old jaw's bottom, face front at the old face's, scale from their distance;
  ids 200 cranium, 201 mandible, 210+ teeth. Its hidden back and crown are cut off and capped.
- every kept part is reduced to its target (fixed numbers below) BEFORE mirroring, so the pairs stay exact;
- symmetry: MM9's body is mirror-symmetric, Meshy's pairs are within 1-3 cm: the right-side parts (the side the
  three-quarter master shows) are mirrored over the left ones. Skirt plates stay as Meshy made them (a mirrored half leaves
  slits between the overlapping plates).
- eyes: the part 19 sphere is reduced and set into the skull's socket (ray cast), mirrored as 119.
Writes object 'Parts' (join of everything, int POINT attribute `pid`; mirrors are 100 + p).
Args: <align blend> <skull parts blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, SKULL, OUT = sys.argv[sys.argv.index('--') + 1:]
MID = -0.0037
RIGHT = [3, 6, 7, 10, 12, 15, 17, 19, 23, 26, 35, 36, 37, 40, 54, 55, 59, 63]
SKIRT = [14, 16, 30, 32, 33, 38, 41, 42, 49, 50, 56, 58, 60, 61, 65]
CENTER = [0, 8, 9, 11, 18, 21, 22, 25, 44, 45, 46, 47, 57] + SKIRT
TARGET = {0: 420, 8: 640, 7: 640, 12: 340, 3: 160, 6: 150, 23: 90, 10: 170, 37: 50, 15: 44, 46: 44, 17: 70, 36: 64, 35: 44,
          59: 40, 9: 110, 44: 24, 11: 130, 45: 30, 18: 130, 21: 170, 22: 70, 19: 32}
CRANIUM, MANDIBLE, TOOTH = 1100, 520, 14
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Meshy']; me = o.data
pa = next(a for a in me.attributes if a.data_type == 'INT' and a.name.startswith('part'))
part = np.zeros(len(me.vertices), int); pa.data.foreach_get('value', part)
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
pairs = [(1, 7), (5, 12), (3, 28), (10, 20), (15, 43)]
mids = [(co[part == a][:, 0].mean() + co[part == b][:, 0].mean()) / 2 for a, b in pairs]
dx = MID - float(np.mean(mids)); print('mid shift', dx)
co[:, 0] += dx
face = co[part == 4]; jaw = co[part == 2]
old = dict(chin=jaw[:, 2].min(), front=min(face[:, 1].min(), jaw[:, 1].min()), x=MID)
eye_old = co[part == 19].mean(0)
print('OLD', old, 'eye', eye_old)


def split(ids_arr, co_arr, mesh, ids):
    """Objects of the wanted loose parts."""
    bm = bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table()
    for v in bm.verts: v.co = Vector(co_arr[v.index])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if ids_arr[v.index] not in ids], context='VERTS')
    m = bpy.data.meshes.new('p'); bm.to_mesh(m); bm.free()
    x = bpy.data.objects.new('p', m); bpy.context.scene.collection.objects.link(x)
    return x


def reduce(x, target, group=None, factor=None):
    n = len(x.data.polygons)
    if n <= target: return x
    bpy.context.view_layer.objects.active = x
    for y in bpy.data.objects: y.select_set(y is x)
    d = x.modifiers.new('d', 'DECIMATE'); d.ratio = target / n; d.use_collapse_triangulate = True
    if group: d.vertex_group = group; d.vertex_group_factor = factor; d.invert_vertex_group = True
    bpy.ops.object.modifier_apply(modifier='d')
    return x


pieces = {}
for p in RIGHT + CENTER:
    x = split(part, co, me, [p])
    pieces[p] = reduce(x, TARGET.get(p, 10 ** 6))
# skull
with bpy.data.libraries.load(SKULL) as (src, dst):
    dst.objects = ['Meshy']
sk = dst.objects[0]; bpy.context.scene.collection.objects.link(sk); sk.name = 'SkullSrc'
sm = sk.data
spa = next(a for a in sm.attributes if a.data_type == 'INT' and a.name.startswith('part'))
sp = np.zeros(len(sm.vertices), int); spa.data.foreach_get('value', sp)
sc = np.zeros(len(sm.vertices) * 3); sm.vertices.foreach_get('co', sc); sc = sc.reshape(-1, 3)
ids = sorted(set(sp.tolist()))
tris = {i: 0 for i in ids}
for f in sm.polygons: tris[sp[f.vertices[0]]] += 1
cran = max(ids, key=lambda i: tris[i]); mand = max((i for i in ids if i != cran), key=lambda i: tris[i])
# scale: skull height to the old chin .. old brow distance over the socket: the old eye height is the common landmark
SOCKET_Z = 0.05                                     # skull units, measured from the front view
scale = (eye_old[2] - old['chin']) / (SOCKET_Z - sc[:, 2].min())
print('skull scale', scale)
place = lambda p: (p - [ (sc[:, 0].min() + sc[:, 0].max()) / 2, sc[:, 1].min(), sc[:, 2].min()]) * scale + [MID, old['front'], old['chin']]
sc2 = place(sc)
print('SKULL bounds', sc2.min(0), sc2.max(0))
x = split(sp, sc2, sm, [cran])
# the helmet hides the crown and the back of the cranium: cut them off (the openings are capped), the face keeps its triangles
bm = bmesh.new(); bm.from_mesh(x.data)
yf = min(v.co.y for v in bm.verts)
for co_, no_ in (((0, yf + 0.125, 0), (0, 1, 0)), ((0, 0, 0.815), (0, 0, 1))):
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co_, plane_no=no_, clear_outer=True)
    edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_boundary]
    nf = bmesh.ops.holes_fill(bm, edges=edges, sides=0)['faces']
    bmesh.ops.triangulate(bm, faces=nf, quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(x.data); bm.free()
print('cranium cut to', len(x.data.polygons))
pieces[200] = reduce(x, CRANIUM)
pieces[201] = reduce(split(sp, sc2, sm, [mand]), MANDIBLE)
k = 210
for i in ids:
    if i in (cran, mand): continue
    pieces[k] = reduce(split(sp, sc2, sm, [i]), TOOTH); k += 1
print('teeth', k - 210)
# eyes in the sockets
crbm = bmesh.new(); crbm.from_mesh(pieces[200].data); bvh = BVHTree.FromBMesh(crbm)
ey = np.array(eye_old); ex = (SOCKET_Z, 0.147)
sx = MID - 0.147 * scale; sz = old['chin'] + (SOCKET_Z - sc[:, 2].min()) * scale
hit = bvh.ray_cast(Vector((sx, old['front'] - 0.1, sz)), Vector((0, 1, 0)))
print('socket floor', hit[0], 'x', sx, 'z', sz)
eye = pieces[19]; ev = np.array([tuple(v.co) for v in eye.data.vertices]); ec = ev.mean(0); er = np.linalg.norm(ev - ec, axis=1).max()
ER = 0.0125
tgt = np.array(hit[0]) + [0, -ER * 0.6, 0]
for v in eye.data.vertices: v.co = Vector((np.array(v.co) - ec) * ER / er + tgt)
# join
parts_all = []
for p, x in pieces.items():
    me2 = x.data
    a = me2.attributes.new('pid', 'INT', 'POINT'); a.data.foreach_set('value', [p] * len(me2.vertices))
    for g in list(x.vertex_groups): x.vertex_groups.remove(g)
    while me2.materials: me2.materials.pop()
    parts_all.append(x)
# mirrors
for p in RIGHT:
    x = pieces[p]; y = x.copy(); y.data = x.data.copy(); bpy.context.scene.collection.objects.link(y)
    bm = bmesh.new(); bm.from_mesh(y.data)
    for v in bm.verts: v.co.x = 2 * MID - v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(y.data); bm.free()
    y.data.attributes['pid'].data.foreach_set('value', [p + 100] * len(y.data.vertices))
    parts_all.append(y)
for y in bpy.data.objects: y.select_set(y in parts_all)
bpy.context.view_layer.objects.active = parts_all[0]
bpy.ops.object.join()
j = bpy.context.active_object; j.name = 'Parts'; j.data.name = 'Parts'
bpy.data.objects.remove(o); bpy.data.objects.remove(sk)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
print('faces', len(j.data.polygons), 'verts', len(j.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
