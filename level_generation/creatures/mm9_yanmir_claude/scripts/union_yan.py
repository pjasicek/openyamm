"""Step B (from mm9_bigfoot_claude/union_bf.py, Yanmir placement): head-only shell on the fitted body as one closed skin by a Boolean union (the voxel wrap of the Gezzampt blurred the face at 3-4 mm). Old head shrunk inside the new one first. The crease where they meet is relaxed, except under the chin. Eyes stay separate pieces. Attribute part: 0 skin, 13 eyes.
Args: <pose blend> <head blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OY, OZ = 0.47, 0.027, 1.098
C = np.array([0.0, -0.03, 1.10]); SHR = 0.55
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']; me = body.data
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
n = 0
for v in me.vertices:
    p = np.array(v.co[:])
    t = sstep(p[2], 0.93, 1.00) * (1 - sstep(abs(p[0]), 0.13, 0.20))
    if t > 0: v.co = Vector(p + t * (SHR - 1) * (p - C)); n += 1
print('SHRUNK', n)
for nm, ob in parts.items():
    bpy.context.scene.collection.objects.link(ob)
face = parts['Face']
Pb = np.array([v.co[:] for v in me.vertices]); Pf = np.array([v.co[:] for v in face.data.vertices])
print('COUNTS', len(Pb), len(Pf))
bm = bmesh.new(); bm.from_mesh(face.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); print('FACE boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold)); bm.to_mesh(face.data); bm.free()
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o is body)
m = body.modifiers.new('U', 'BOOLEAN'); m.operation = 'UNION'; m.object = face; m.solver = 'EXACT'
try: m.use_self = False; m.use_hole_tolerant = True      # the voxel-closed body self-intersects in folds: use_self turned those into 1580 multi-face edges
except Exception as e: print('opt', e)
bpy.ops.object.modifier_apply(modifier=m.name)
print('UNION verts', len(me.vertices), 'polys', len(me.polygons))
kb = KDTree(len(Pb)); [kb.insert(Vector(p), i) for i, p in enumerate(Pb)]; kb.balance()
kf = KDTree(len(Pf)); [kf.insert(Vector(p), i) for i, p in enumerate(Pf)]; kf.balance()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-4)
bd = [e for e in bm.edges if e.is_boundary]
if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=12)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('MAN nonmanifold', sum(1 for e in bm.edges if not e.is_manifold), 'boundary', sum(1 for e in bm.edges if e.is_boundary))
bm.verts.ensure_lookup_table()
new = [v for v in bm.verts if kb.find(v.co)[2] > 1e-4 and kf.find(v.co)[2] > 1e-4]
print('NEW verts', len(new))
ring = set(new)
fr = set(new)
for _ in range(5):
    fr = {e.other_vert(v) for v in fr for e in v.link_edges} - ring
    ring |= fr
band = [v for v in ring if not (v.co.y < -0.15 and v.co.z < 1.05)]      # no relaxing under the beard
for _ in range(10):
    nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in band]
    for v, c in nw: v.co = v.co * 0.45 + c * 0.55
lay = bm.verts.layers.int.new('part')
ey = parts['Eyes'].data
nv = [bm.verts.new(v.co[:]) for v in ey.vertices]
for v in nv: v[lay] = 13
for p in ey.polygons:
    try: bm.faces.new([nv[i] for i in p.vertices])
    except ValueError: pass
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
for ob in parts.values(): bpy.data.objects.remove(ob)
for p in me.polygons: p.use_smooth = True
print('FINAL verts', len(me.vertices), 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
