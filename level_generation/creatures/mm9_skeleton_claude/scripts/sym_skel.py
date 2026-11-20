"""Clean the Meshy parts (all in the HD master's A-pose, moved onto the MM9 scale: Meshy unit x 1.85, hip height and skull top as MM9's):
- the extra sixth digit (42, 71 on the right, 89, 120 on the left: a fork off the little finger, Smart Topology misread the hand) goes;
- the body's coarse skull (16) goes; the skull-only Smart Topology replaces it: cranium 2000, mandible 2001, teeth 2010+. Its inner shell
  (part 3, it pokes through the crown) goes. The sockets are closed shallow dishes, so they are deepened before reduction; eyes 2002 (right)
  and 2003 (left) are spheres set in them by ray casting;
- every kept part is reduced to its target BEFORE mirroring, so the pairs stay exact;
- symmetry: MM9's body is mirror-symmetric, Meshy's pairs are within 1-2 cm: the right-side parts (x < 0, the side the three-quarter master shows)
  are mirrored over the left (pid 1000 + p). The diagonal strap (14, 95), the scrap 124, ribs 18, pelvis 36 and the rope stay single;
- a back panel (300) and a rope collar (301): the masters and MM9 have a vest closed across the upper back and a rope at the neck, Smart Topology
  gave only the two flanks. The panel lies on the ribs and spine by ray casting, with a torn hem; the collar is a tube round the neck base. Both are painted by the retexture.
Writes object 'Parts' (join, int POINT attribute `pid`). Args: <body parts blend> <skull parts blend> <out blend>"""
import bpy, bmesh, sys, math, random
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, SKULL, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OFF = 1.85, np.array([0.0, -0.02, -0.234])
RATIO, MINT = 0.56, 18
TARGET = {18: 860, 36: 480, 13: 230, 2: 70, 47: 36, 14: 90, 95: 80, 44: 96, 76: 90, 65: 120, 30: 90, 11: 80, 146: 60, 87: 50, 22: 60, 26: 40, 81: 44,
          41: 56, 54: 64, 74: 40, 3: 44, 93: 30, 6: 40, 108: 40}
CENTER = [18, 36, 13, 97, 64, 78, 123, 25, 102, 31, 38, 115, 126, 68, 92, 10, 61, 0, 83, 14, 95, 124]
DROP = {16, 42, 71, 89, 120, 151}
CRANIUM, MANDIBLE, TOOTH = 2100, 600, 16
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Meshy']; me = o.data
pa = next(a for a in me.attributes if a.data_type == 'INT' and a.name.startswith('part'))
part = np.zeros(len(me.vertices), int); pa.data.foreach_get('value', part)
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
pairs = [(65, 34), (30, 37), (44, 112), (76, 12), (146, 40), (81, 113)]
mid = float(np.mean([(co[part == a][:, 0].mean() + co[part == b][:, 0].mean()) / 2 for a, b in pairs]))
print('mid', mid)
hd = co[part == 16]
old = dict(chin=hd[:, 2].min(), front=hd[:, 1].min(), top=hd[:, 2].max())
print('OLD head', old)
co2 = (co - [mid, 0, 0]) * S + OFF
ids = sorted(set(part.tolist()))
cen = {i: co[part == i].mean(0) for i in ids}
RIGHT = [i for i in ids if i not in CENTER and i not in DROP and cen[i][0] - mid < 0]
LEFT = [i for i in ids if i not in CENTER and i not in DROP and cen[i][0] - mid >= 0]
print('right', len(RIGHT), 'left dropped', len(LEFT))


def split(ids_arr, co_arr, mesh, ids_):
    bm = bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table()
    for v in bm.verts: v.co = Vector(co_arr[v.index])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if ids_arr[v.index] not in ids_], context='VERTS')
    m = bpy.data.meshes.new('p'); bm.to_mesh(m); bm.free()
    x = bpy.data.objects.new('p', m); bpy.context.scene.collection.objects.link(x)
    return x


def reduce(x, target):
    n = len(x.data.polygons)
    if n <= target: return x
    bpy.context.view_layer.objects.active = x
    for y in bpy.data.objects: y.select_set(y is x)
    d = x.modifiers.new('d', 'DECIMATE'); d.ratio = target / n; d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='d')
    return x


pieces = {}
for p in RIGHT + CENTER:
    x = split(part, co2, me, [p])
    n = len(x.data.polygons)
    t = TARGET.get(p, max(MINT, int(round(n * RATIO))))
    pieces[p] = reduce(x, t)
# --- skull
with bpy.data.libraries.load(SKULL) as (src, dst):
    dst.objects = ['Meshy']
sk = dst.objects[0]; bpy.context.scene.collection.objects.link(sk); sk.name = 'SkullSrc'
sm = sk.data
spa = next(a for a in sm.attributes if a.data_type == 'INT' and a.name.startswith('part'))
sp = np.zeros(len(sm.vertices), int); spa.data.foreach_get('value', sp)
sc = np.zeros(len(sm.vertices) * 3); sm.vertices.foreach_get('co', sc); sc = sc.reshape(-1, 3)
sids = sorted(set(sp.tolist()))
tris = {i: 0 for i in sids}
for f in sm.polygons: tris[sp[f.vertices[0]]] += 1
CRAN, MAND, SHELL = 0, 4, 3
assert tris[CRAN] > 9000 and tris[MAND] > 2500 and tris[SHELL] > 1000
# sockets: closed dishes in the skull's own units, deepened before reduction
SOCK = [(-0.172, -0.04), (0.164, -0.04)]
keep = sp == CRAN
sc3 = sc.copy()
for cx, cz in SOCK:
    r2 = ((sc[:, 0] - cx) / 0.105) ** 2 + ((sc[:, 2] - cz) / 0.09) ** 2
    m = keep & (r2 < 1) & (sc[:, 1] < -0.1)
    sc3[m, 1] += 0.085 * (1 - r2[m]) ** 0.7
    print('socket verts', int(m.sum()))
hs = float(sc[:, 2].max() - sc[:, 2].min())
scale = (old['top'] - old['chin']) / hs * S
place = lambda p: (p - [(sc[:, 0].min() + sc[:, 0].max()) / 2, sc[:, 1].min(), sc[:, 2].min()]) * scale + (np.array([0, old['front'], old['chin']]) * S + OFF)
sc2 = place(sc3)
print('SKULL scale', scale, 'bounds', sc2.min(0), sc2.max(0))
pieces[2000] = reduce(split(sp, sc2, sm, [CRAN]), CRANIUM)
pieces[2001] = reduce(split(sp, sc2, sm, [MAND]), MANDIBLE)
k = 2010
for i in sids:
    if i in (CRAN, MAND, SHELL): continue
    pieces[k] = reduce(split(sp, sc2, sm, [i]), TOOTH); k += 1
print('teeth', k - 2010)
# eyes
crbm = bmesh.new(); crbm.from_mesh(pieces[2000].data); bvh = BVHTree.FromBMesh(crbm)
ER = 0.0125
for (cx, cz), pid_ in zip(SOCK, (2002, 2003)):
    p0 = place(np.array([[cx, sc[:, 1].min() - 0.2, cz]]))[0]
    hit = bvh.ray_cast(Vector(p0), Vector((0, 1, 0)))
    print('socket floor', hit[0])
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=ER)
    for v in bm.verts: v.co += hit[0] + Vector((0, -ER * 0.1, 0))
    m = bpy.data.meshes.new('eye'); bm.to_mesh(m); bm.free()
    x = bpy.data.objects.new('eye', m); bpy.context.scene.collection.objects.link(x); pieces[pid_] = x
# --- back panel: laid on ribs, spine and flanks
tree_ids = [18, 102, 31, 38, 2, 47, 25, 64]
bb = bmesh.new()
for p in tree_ids:
    bb.from_mesh(pieces[p].data)
b2 = BVHTree.FromBMesh(bb)
NX, NZ = 13, 9
XE = 0.118
top = lambda x_: 0.392 - 2.2 * x_ * x_
xs = np.linspace(-XE, XE, NX); zs = np.linspace(0.388, 0.165, NZ)
G = np.zeros((NZ, NX))
for j, z in enumerate(zs):
    for i, x_ in enumerate(xs):
        ys = []
        for dx in (-0.03, -0.015, 0, 0.015, 0.03):
            for dz in (-0.03, 0, 0.03):
                h = b2.ray_cast(Vector((x_ + dx, 0.6, z + dz)), Vector((0, -1, 0)))
                if h[0] is not None: ys.append(h[0].y)
        G[j, i] = max(ys) if ys else np.nan
G = np.where(np.isnan(G), np.nanmin(G), G)
K = np.array([0.27, 0.46, 0.27])
for _ in range(3):
    G = np.apply_along_axis(lambda r: np.convolve(np.r_[r[0], r, r[-1]], K, 'valid'), 1, G)
    G = np.apply_along_axis(lambda r: np.convolve(np.r_[r[0], r, r[-1]], K, 'valid'), 0, G)
G = G + 0.016
random.seed(9)
hem = []
for i, x_ in enumerate(xs):
    side = abs(x_) / XE
    hem.append(0.20 + 0.05 * (1 - side) + random.uniform(0.0, 0.05) * (i % 2 == 0) - 0.035 * (i % 2 == 1))   # jagged, higher over the spine
bm = bmesh.new(); vg = {}
for j in range(NZ):
    t = j / (NZ - 1)
    for i, x_ in enumerate(xs):
        z = top(x_) + (hem[i] - top(x_)) * t
        vg[(j, i)] = bm.verts.new((x_, float(G[j, i]) + 0.0, z))
for j in range(NZ - 1):
    for i in range(NX - 1):
        a_, b_, c_, d_ = vg[(j, i)], vg[(j, i + 1)], vg[(j + 1, i + 1)], vg[(j + 1, i)]
        if (i + j) % 2:
            bm.faces.new((a_, c_, b_)); bm.faces.new((a_, d_, c_))
        else:
            bm.faces.new((a_, d_, b_)); bm.faces.new((b_, d_, c_))
m = bpy.data.meshes.new('back'); bm.to_mesh(m); bm.free()
x = bpy.data.objects.new('back', m); bpy.context.scene.collection.objects.link(x); pieces[300] = x
# --- rope collar
C = np.array([0.0, 0.058, 0.392]); RX, RY, TILT, TR = 0.092, 0.082, 0.012, 0.0115
NU, NV = 22, 6
bm = bmesh.new(); ring = []
for u in range(NU):
    a_ = 2 * math.pi * u / NU
    p = C + [RX * math.cos(a_), RY * math.sin(a_), TILT * math.sin(a_) - 0.016 * max(0.0, -math.sin(a_)) ** 2]
    rad = np.array([math.cos(a_), math.sin(a_), 0.0]); up = np.array([0, 0, 1.0])
    ring.append([bm.verts.new(tuple(p + TR * (math.cos(2 * math.pi * v / NV) * rad + math.sin(2 * math.pi * v / NV) * up))) for v in range(NV)])
for u in range(NU):
    for v in range(NV):
        a_, b_, c_, d_ = ring[u][v], ring[(u + 1) % NU][v], ring[(u + 1) % NU][(v + 1) % NV], ring[u][(v + 1) % NV]
        bm.faces.new((a_, b_, c_)); bm.faces.new((a_, c_, d_))
m = bpy.data.meshes.new('collar'); bm.to_mesh(m); bm.free()
x = bpy.data.objects.new('collar', m); bpy.context.scene.collection.objects.link(x); pieces[301] = x
# --- join
parts_all = []
for p, x in pieces.items():
    me2 = x.data
    a = me2.attributes.new('pid', 'INT', 'POINT'); a.data.foreach_set('value', [p] * len(me2.vertices))
    for g in list(x.vertex_groups): x.vertex_groups.remove(g)
    while me2.materials: me2.materials.pop()
    parts_all.append(x)
for p in RIGHT:
    x = pieces[p]; y = x.copy(); y.data = x.data.copy(); bpy.context.scene.collection.objects.link(y)
    bm = bmesh.new(); bm.from_mesh(y.data)
    for v in bm.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(y.data); bm.free()
    y.data.attributes['pid'].data.foreach_set('value', [p + 1000] * len(y.data.vertices))
    parts_all.append(y)
for y in bpy.data.objects: y.select_set(y in parts_all)
bpy.context.view_layer.objects.active = parts_all[0]
bpy.ops.object.join()
j = bpy.context.active_object; j.name = 'Parts'; j.data.name = 'Parts'
for n in ('Meshy', 'SkullSrc'):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
print('faces', len(j.data.polygons), 'verts', len(j.data.vertices))
v = np.array([tuple(x.co) for x in j.data.vertices]); print('bounds', v.min(0), v.max(0))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
